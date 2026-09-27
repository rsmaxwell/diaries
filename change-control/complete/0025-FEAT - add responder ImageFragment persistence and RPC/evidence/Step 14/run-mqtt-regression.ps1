#Requires -Version 7.0
param([Parameter(Mandatory)][string]$EvidenceDirectory)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../../../..')).Path
$evidence=(New-Item -ItemType Directory $EvidenceDirectory -ErrorAction Stop).FullName
$previous=$env:DIARIES_IMAGE_MQTT_TEST_URL
$results=@()
try {
    foreach ($test in @('ImageCatalogueMqttIntegrationTest','SynchroniseLargeRetainedTreeMqttIntegrationTest')) {
        $name='diaries-0025-step14-'+[guid]::NewGuid().ToString('N').Substring(0,12)
        $owned=$false
        $result=[ordered]@{test=$test;status='RUNNING';container=$name}
        $dir=New-Item -ItemType Directory (Join-Path $evidence $test)
        try {
            $config=Join-Path $root 'config/mosquitto/mosquitto-large-tree-test.conf'
            Copy-Item -LiteralPath $config -Destination (Join-Path $dir 'mosquitto.conf')
            $image=& docker image inspect eclipse-mosquitto:2 --format '{{.Id}}'
            if($LASTEXITCODE){throw 'Image inspection failed'}
            $result.imageId=$image
            & docker run -d --rm --name $name -p '127.0.0.1::1883' --mount "type=bind,source=$config,target=/mosquitto/config/mosquitto.conf,readonly" $image | Set-Content (Join-Path $dir 'container.txt')
            if($LASTEXITCODE){throw 'Broker startup failed'}
            $owned=$true
            $binding=(& docker port $name 1883).Trim()
            if($binding -notmatch '^127\.0\.0\.1:[0-9]+$'){throw 'Unexpected binding'}
            $env:DIARIES_IMAGE_MQTT_TEST_URL="tcp://$binding"
            & (Join-Path $root 'gradlew.bat') -p $root :diaries-responder:test --tests "com.rsmaxwell.diaries.responder.sync.$test" --rerun-tasks --console=plain *> (Join-Path $dir 'gradle.log')
            $exitCode=$LASTEXITCODE
            $report=Join-Path $root "diaries-responder/build/test-results/test/TEST-com.rsmaxwell.diaries.responder.sync.$test.xml"
            if(Test-Path $report){Copy-Item -LiteralPath $report -Destination (Join-Path $dir 'test.xml')}
            if($exitCode){throw "Gradle exit $exitCode"}
            [xml]$xml=Get-Content $report -Raw
            $result.tests=[int]$xml.testsuite.tests
            $result.skipped=[int]$xml.testsuite.skipped
            if($result.tests -ne 1 -or $result.skipped -or [int]$xml.testsuite.failures -or [int]$xml.testsuite.errors){throw 'Expected one non-skipped passing test'}
            $result.status='PASSED'
        } catch {$result.status='FAILED';$result.error=$_.Exception.Message;throw}
        finally {
            if($owned){
                & docker logs $name *> (Join-Path $dir 'broker.log')
                & docker stop $name | Set-Content (Join-Path $dir 'cleanup.log')
                $result.cleanupExitCode=$LASTEXITCODE
                if($LASTEXITCODE){$result.status='CLEANUP_FAILED'}
            }
            $results+= $result
            $result | ConvertTo-Json | Set-Content (Join-Path $dir 'result.json')
        }
    }
} finally {
    $env:DIARIES_IMAGE_MQTT_TEST_URL=$previous
    $results | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $evidence 'results.json')
}
