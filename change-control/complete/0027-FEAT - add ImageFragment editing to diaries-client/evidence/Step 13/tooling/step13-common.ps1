Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-DiariesProjectRoot {
    param([string]$StartPath = $PSScriptRoot)
    $current = [System.IO.Path]::GetFullPath($StartPath)
    if (Test-Path -LiteralPath $current -PathType Leaf) {
        $current = Split-Path -Parent $current
    }
    while ($true) {
        $client = Join-Path $current 'diaries-client'
        $responder = Join-Path $current 'diaries-responder'
        $changeControl = Join-Path $current 'change-control'
        if ((Test-Path -LiteralPath $client -PathType Container) -and
            (Test-Path -LiteralPath $responder -PathType Container) -and
            (Test-Path -LiteralPath $changeControl -PathType Container)) {
            return $current
        }
        $parent = Split-Path -Parent $current
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
            throw "Could not locate the Diaries project root from $StartPath"
        }
        $current = $parent
    }
}

function Get-Step13BuildRoot {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    return (Join-Path $ProjectRoot 'build\0027-step13')
}

function Get-CurrentStep13RunDirectory {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $buildRoot = Get-Step13BuildRoot -ProjectRoot $ProjectRoot
    $marker = Join-Path $buildRoot 'current-run.txt'
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        throw "No Step 13 run is active. Run step13-begin.ps1 first: $marker"
    }
    $runId = (Get-Content -LiteralPath $marker -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($runId)) {
        throw "Step 13 run marker is empty: $marker"
    }
    $runDirectory = Join-Path (Join-Path $buildRoot 'runs') $runId
    if (-not (Test-Path -LiteralPath $runDirectory -PathType Container)) {
        throw "Step 13 run directory does not exist: $runDirectory"
    }
    return $runDirectory
}

function Read-DotEnv {
    param([Parameter(Mandatory=$true)][string]$Path)
    $map = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $map
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith('#')) { continue }
        $idx = $trimmed.IndexOf('=')
        if ($idx -lt 1) { continue }
        $name = $trimmed.Substring(0,$idx).Trim()
        $value = $trimmed.Substring($idx+1).Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1,$value.Length-2)
        }
        $map[$name] = $value
    }
    return $map
}

function Get-EffectiveDevelopmentEnvironment {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $modePath = Join-Path $ProjectRoot 'config\environments\development-infrastructure.env'
    $localPath = Join-Path $ProjectRoot 'config\environments\local.env'
    if (-not (Test-Path -LiteralPath $modePath -PathType Leaf)) { throw "Missing $modePath" }
    if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) { throw "Missing $localPath" }
    $result = @{}
    foreach ($entry in (Read-DotEnv -Path $modePath).GetEnumerator()) { $result[$entry.Key]=$entry.Value }
    foreach ($entry in (Read-DotEnv -Path $localPath).GetEnumerator()) { $result[$entry.Key]=$entry.Value }
    return $result
}

function Get-BaseResponderConfigPath {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    if (-not [string]::IsNullOrWhiteSpace($env:DIARIES_RESPONDER_BASE_CONFIG_FILE)) {
        return [System.IO.Path]::GetFullPath($env:DIARIES_RESPONDER_BASE_CONFIG_FILE)
    }
    if (-not [string]::IsNullOrWhiteSpace($env:DIARIES_RESPONDER_CONFIG_FILE)) {
        return [System.IO.Path]::GetFullPath($env:DIARIES_RESPONDER_CONFIG_FILE)
    }
    return (Join-Path $env:USERPROFILE '.diaries\responder.json')
}

function Get-EffectiveFilesRoot {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $effective = Get-EffectiveDevelopmentEnvironment -ProjectRoot $ProjectRoot
    if (-not $effective.ContainsKey('DIARIES_FILES_DIR')) { throw 'DIARIES_FILES_DIR is not configured.' }
    $baseConfigPath = Get-BaseResponderConfigPath -ProjectRoot $ProjectRoot
    if (-not (Test-Path -LiteralPath $baseConfigPath -PathType Leaf)) { throw "Responder base configuration not found: $baseConfigPath" }
    $config = Get-Content -LiteralPath $baseConfigPath -Raw | ConvertFrom-Json
    if ($null -eq $config.diaries -or [string]::IsNullOrWhiteSpace([string]$config.diaries.root)) {
        throw "Responder base configuration does not define diaries.root: $baseConfigPath"
    }
    return [System.IO.Path]::GetFullPath((Join-Path ([string]$config.diaries.root) ([string]$effective['DIARIES_FILES_DIR'])))
}

function Get-ContainerEnvironment {
    param([Parameter(Mandatory=$true)][string]$ContainerName)
    $lines = & docker inspect $ContainerName --format '{{range .Config.Env}}{{println .}}{{end}}' 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Could not inspect container $ContainerName" }
    $map=@{}
    foreach($line in $lines) {
        $idx=$line.IndexOf('=')
        if($idx -gt 0){ $map[$line.Substring(0,$idx)]=$line.Substring($idx+1) }
    }
    return $map
}

function Invoke-Step13Sql {
    param(
        [Parameter(Mandatory=$true)][string]$Sql,
        [string]$ContainerName='diaries-development-db'
    )
    $containerEnv = Get-ContainerEnvironment -ContainerName $ContainerName
    $user = if($containerEnv.ContainsKey('POSTGRES_USER')){$containerEnv['POSTGRES_USER']}else{'diaries'}
    $db = if($containerEnv.ContainsKey('POSTGRES_DB')){$containerEnv['POSTGRES_DB']}else{'diaries'}
    $output = & docker exec $ContainerName psql -X -v ON_ERROR_STOP=1 -U $user -d $db -A -F '|' -P footer=off -c $Sql 2>&1
    if ($LASTEXITCODE -ne 0) { throw "psql failed: $($output -join [Environment]::NewLine)" }
    return $output
}

function Get-ClientMqttConfig {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $configPath = Join-Path $ProjectRoot 'diaries-client\public\assets\config.json'
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) { throw "Missing client config: $configPath" }
    return (Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json)
}

function Capture-RetainedTopic {
    param(
        [Parameter(Mandatory=$true)][string]$Topic,
        [Parameter(Mandatory=$true)]$ClientConfig,
        [string]$ContainerName='diaries-development-mqtt'
    )
    if ([string]::IsNullOrWhiteSpace([string]$ClientConfig.username) -or
        [string]::IsNullOrWhiteSpace([string]$ClientConfig.password)) {
        throw 'Client MQTT username/password are missing from diaries-client/public/assets/config.json.'
    }
    $output = & docker exec $ContainerName mosquitto_sub -h localhost -p 1883 -u ([string]$ClientConfig.username) -P ([string]$ClientConfig.password) -t $Topic -C 1 -W 2 -v 2>&1
    $code = $LASTEXITCODE
    if ($code -eq 0) { return ($output -join [Environment]::NewLine) }
    # mosquitto_sub returns a timeout status when the exact topic has no retained value.
    if ($code -eq 27 -or $code -eq 1) {
        return '<no retained message received within 2 seconds>'
    }
    throw "mosquitto_sub failed for $Topic (exit $code): $($output -join [Environment]::NewLine)"
}

function Write-Utf8NoBom {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Text)
    $parent=Split-Path -Parent $Path
    if(-not (Test-Path -LiteralPath $parent -PathType Container)){ New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $utf8=New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Text,$utf8)
}
