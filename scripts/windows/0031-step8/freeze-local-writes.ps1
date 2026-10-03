param(
    [string]$EvidenceDirectory
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir '..\..\..'))
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

if ([string]::IsNullOrWhiteSpace($EvidenceDirectory)) {
    $EvidenceDirectory = Join-Path $ProjectDir "change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 8\runtime"
}
$EvidenceDirectory = [System.IO.Path]::GetFullPath($EvidenceDirectory)
New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
$EvidenceFile = Join-Path $EvidenceDirectory "local-write-freeze-$Timestamp.txt"

$KnownResponderContainers = @(
    'diaries-local-responder',
    'diaries-published-smoke-responder'
)

function Write-Evidence {
    param([string]$Message = '')
    $Message | Tee-Object -FilePath $EvidenceFile -Append
}


function Get-TcpListeners {
    param([Parameter(Mandatory = $true)][int]$Port)
    try {
        return @(
            [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() |
                Where-Object { $_.Port -eq $Port }
        )
    } catch {
        throw "Unable to query TCP/$Port listeners using the .NET network-information API: $($_.Exception.Message)"
    }
}

function Get-RunningContainerNames {
    $output = & docker ps --format '{{.Names}}' 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "docker ps failed: $($output -join [Environment]::NewLine)"
    }
    return @($output | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

Write-Evidence "0031-FEAT Step 8 - local mutable-write freeze"
Write-Evidence "Captured: $(Get-Date -Format o)"
Write-Evidence "Host: $env:COMPUTERNAME"
Write-Evidence "Project: $ProjectDir"
Write-Evidence
Write-Evidence 'The responder is the only component permitted to mutate catalogue Files.'
Write-Evidence 'Known local Docker responders will be stopped. A remaining listener on TCP/8081 blocks completion.'
Write-Evidence

$running = Get-RunningContainerNames
foreach ($container in $KnownResponderContainers) {
    if ($running -contains $container) {
        Write-Evidence "Stopping local responder container: $container"
        $stopOutput = & docker stop $container 2>&1
        $stopOutput | ForEach-Object { Write-Evidence "  $_" }
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to stop responder container: $container"
        }
    } else {
        Write-Evidence "Responder container already stopped/not running: $container"
    }
}

Start-Sleep -Milliseconds 500
$runningAfter = Get-RunningContainerNames
foreach ($container in $KnownResponderContainers) {
    if ($runningAfter -contains $container) {
        throw "Responder container is still running after stop: $container"
    }
}

$listeners = @(Get-TcpListeners -Port 8081)

if ($listeners.Count -gt 0) {
    Write-Evidence
    Write-Evidence 'BLOCKED: TCP/8081 is still listening after Docker responders were stopped.'
    foreach ($listener in $listeners) {
        Write-Evidence ("  LocalAddress={0} LocalPort={1}" -f $listener.Address, $listener.Port)
    }
    Write-Evidence 'This is commonly the direct Windows development responder. Stop that responder and run this script again.'
    throw 'Mutable-write freeze is not proven because TCP/8081 is still listening.'
}

$gitCommit = 'unknown'
try {
    $candidate = (& git -C $ProjectDir rev-parse HEAD 2>$null | Select-Object -First 1)
    if (-not [string]::IsNullOrWhiteSpace($candidate)) { $gitCommit = $candidate.Trim() }
} catch { }

Write-Evidence
Write-Evidence 'PASS: no known local Docker responder is running.'
Write-Evidence 'PASS: no process is listening on local TCP/8081.'
Write-Evidence "Diaries source commit: $gitCommit"
Write-Evidence 'Local mutable Image/File writes are frozen.'
Write-Evidence 'Leave the responder stopped until the pre-migration capture/reconciliation sequence says it is safe to restart.'
Write-Evidence "Evidence: $EvidenceFile"
