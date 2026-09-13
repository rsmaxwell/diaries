[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ResponderJar,
    [Parameter(Mandatory)][string]$OutputDirectory,
    [Parameter(Mandatory)][string]$WorkDirectory,
    [string]$BrokerImage = 'eclipse-mosquitto@sha256:6f8d8a947c506f8a2290ec65cd4bd2bc7cb4d43fb5f6271f861cb013e2ef9797'
)
$ErrorActionPreference = 'Stop'
$jar = (Resolve-Path -LiteralPath $ResponderJar).Path
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
$workPath = [IO.Path]::GetFullPath($WorkDirectory)
$repository = [IO.DirectoryInfo]::new($PSScriptRoot)
while ($repository -and !(Test-Path -LiteralPath (Join-Path $repository.FullName 'gradlew.bat'))) {
    $repository = $repository.Parent
}
if (!$repository) { throw 'Cannot locate the Diaries repository' }
$repositoryPrefix = $repository.FullName.TrimEnd('\') + '\'
foreach ($destination in @($outputPath, $workPath)) {
    if (!$destination.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Capture output and work directories must be inside the Diaries repository'
    }
    if (Test-Path -LiteralPath $destination) { throw "Refusing to overwrite existing directory: $destination" }
}
if ($outputPath -eq $workPath -or $outputPath.StartsWith($workPath + '\', [StringComparison]::OrdinalIgnoreCase) -or
    $workPath.StartsWith($outputPath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Use separate output and work directories' }
$containerName = 'diaries-0024-rpc-' + [guid]::NewGuid().ToString('N')
$mount = 'type=bind,source=' + (Join-Path $PSScriptRoot 'mosquitto.conf') + ',target=/mosquitto/config/mosquitto.conf,readonly'
$containerId = $null
try {
    $started = & docker run --detach --rm --name $containerName --label diaries.change=0024 `
        --publish 127.0.0.1:18884:1883 --tmpfs /mosquitto/data --tmpfs /mosquitto/log --mount $mount $BrokerImage
    if ($LASTEXITCODE -ne 0) { throw 'Disposable broker failed to start; check that port 18884 is free' }
    $containerId = $started.Trim()
    $imageId = & docker inspect $containerId --format '{{.Image}}'
    if ($LASTEXITCODE -ne 0) { throw 'Could not record broker image identity' }
    $captureLines = & java ('-Dlog4j2.configurationFile=' + (Join-Path $PSScriptRoot 'log4j2.xml')) `
        -cp $jar (Join-Path $PSScriptRoot 'CaptureFileRpc.java') $outputPath $workPath 2>&1
    $captureExit = $LASTEXITCODE
    $captureLines | ForEach-Object { Write-Output $_ }
    if ($captureExit -ne 0) { throw "Capture failed with exit code $captureExit; preserve partial output for diagnosis" }
    $captureLines | Set-Content -LiteralPath (Join-Path $outputPath 'capture-console.txt') -Encoding utf8
    [ordered]@{
        jar = $jar; jar_sha256 = (Get-FileHash -LiteralPath $jar -Algorithm SHA256).Hash.ToLowerInvariant()
        broker_image = $BrokerImage; broker_image_id = $imageId.Trim()
        broker_binding = '127.0.0.1:18884'; database_access = $false
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputPath 'runner-provenance.json') -Encoding utf8
    & node (Join-Path $PSScriptRoot 'verify-compatibility.cjs') $outputPath
    if ($LASTEXITCODE -ne 0) { throw 'Capture verification failed' }
} finally {
    if ($containerId) {
        & docker stop $containerId
        if ($LASTEXITCODE -ne 0) { Write-Warning "Could not stop this capture's broker: $containerId" }
    }
}
# Fixture files are left in the explicitly chosen work directory for inspection.
# No database restore, development service stop or recursive filesystem cleanup occurs.
