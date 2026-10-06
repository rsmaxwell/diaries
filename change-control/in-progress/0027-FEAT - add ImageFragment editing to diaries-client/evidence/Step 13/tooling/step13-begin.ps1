param([string]$ProjectRoot)
. (Join-Path $PSScriptRoot 'step13-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot=[System.IO.Path]::GetFullPath($ProjectRoot)
$buildRoot=Get-Step13BuildRoot -ProjectRoot $ProjectRoot
$runId=Get-Date -Format 'yyyyMMdd-HHmmss'
$runDir=Join-Path (Join-Path $buildRoot 'runs') $runId
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
Write-Utf8NoBom -Path (Join-Path $buildRoot 'current-run.txt') -Text ($runId+[Environment]::NewLine)
$metadata=@()
$metadata += "runId=$runId"
$metadata += "startedLocal=$((Get-Date).ToString('o'))"
$metadata += "projectRoot=$ProjectRoot"
try { $metadata += "gitCommit=$((& git -C $ProjectRoot rev-parse HEAD 2>$null) -join '')" } catch { $metadata += 'gitCommit=<unavailable>' }
try {
    $status=& git -C $ProjectRoot status --short 2>$null
    if($status){
        $metadata += 'gitStatus=dirty'
        $metadata += 'gitStatusEntries:'
        $metadata += $status
    } else { $metadata += 'gitStatus=clean' }
} catch { $metadata += 'gitStatus=<unavailable>' }
Write-Utf8NoBom -Path (Join-Path $runDir 'run-metadata.txt') -Text (($metadata -join [Environment]::NewLine)+[Environment]::NewLine)
Write-Host "Step 13 live-evidence run created: $runId"
Write-Host "Run directory: $runDir"
Write-Host 'No responder configuration or credentials are copied into the run directory.'
Write-Output $runDir
