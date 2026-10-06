param(
    [Parameter(Mandatory=$true)][string]$Path,
    [string]$OutputName = 'rpc-diagnostics.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'step13-common.ps1')

$projectRoot = Find-DiariesProjectRoot -StartPath $PSScriptRoot
$runDirectory = Get-CurrentStep13RunDirectory -ProjectRoot $projectRoot
$source = [System.IO.Path]::GetFullPath($Path)

if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Step 13 RPC diagnostic JSON not found: $source"
}
if ([System.IO.Path]::GetExtension($OutputName) -ne '.json') {
    throw 'OutputName must end in .json'
}

$raw = Get-Content -LiteralPath $source -Raw
if ($raw -match '(?i)"(?:accessToken|refreshToken|password|mqttPassword)"\s*:') {
    throw 'Diagnostic JSON contains a forbidden authentication/password key.'
}
if ($raw -match '(?i)"text"\s*:') {
    throw 'Diagnostic JSON contains a raw text field. Step 13 evidence must store textLength only.'
}

try {
    $document = $raw | ConvertFrom-Json
} catch {
    throw "Diagnostic file is not valid JSON: $($_.Exception.Message)"
}

function Get-JsonPropertyValue {
    param(
        [Parameter(Mandatory=$true)]$Object,
        [Parameter(Mandatory=$true)][string]$Name
    )
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

$entriesValue = Get-JsonPropertyValue -Object $document -Name 'entries'
if ($null -eq $entriesValue) {
    throw 'Diagnostic JSON does not contain an entries array.'
}
$entries = @($entriesValue)
if ($entries.Count -eq 0) {
    throw 'Diagnostic JSON contains no entries.'
}

function Find-RpcDiagnosticEntry {
    param(
        [Parameter(Mandatory=$true)][string]$Function,
        [Parameter(Mandatory=$true)][int]$StatusCode,
        [string[]]$ImageIdStates = @()
    )

    foreach ($entry in $entries) {
        if ([string](Get-JsonPropertyValue -Object $entry -Name 'function') -ne $Function) { continue }
        $status = Get-JsonPropertyValue -Object $entry -Name 'status'
        if ($null -eq $status) { continue }
        $code = Get-JsonPropertyValue -Object $status -Name 'code'
        if ($null -eq $code -or [int]$code -ne $StatusCode) { continue }
        if ($ImageIdStates.Count -gt 0) {
            $args = Get-JsonPropertyValue -Object $entry -Name 'args'
            if ($null -eq $args) { continue }
            $state = [string](Get-JsonPropertyValue -Object $args -Name 'imageIdState')
            if ($ImageIdStates -notcontains $state) { continue }
        }
        return $entry
    }
    return $null
}

$required = @(
    [pscustomobject]@{ Name='Phase A addImageFragment -> 403'; Function='addImageFragment'; Code=403; States=@('positive','null','omitted') },
    [pscustomobject]@{ Name='Phase A image-reference updateFragment -> 403'; Function='updateFragment'; Code=403; States=@('positive','null') },
    [pscustomobject]@{ Name='Phase B addImageFragment -> 200'; Function='addImageFragment'; Code=200; States=@('positive','null','omitted'); RequireCommittedFragment=$true },
    [pscustomobject]@{ Name='Phase B updateFragment positive imageId -> 200'; Function='updateFragment'; Code=200; States=@('positive') },
    [pscustomobject]@{ Name='Phase B updateFragment imageId:null -> 200'; Function='updateFragment'; Code=200; States=@('null') }
)

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add('Step 13 redacted RPC diagnostic validation')
$summary.Add("Source: $source")
$summary.Add("Entries: $($entries.Count)")
$summary.Add('')

$missing = New-Object System.Collections.Generic.List[string]
foreach ($item in $required) {
    $match = Find-RpcDiagnosticEntry -Function $item.Function -StatusCode $item.Code -ImageIdStates $item.States
    $requiresCommittedFragment = [bool](Get-JsonPropertyValue -Object $item -Name 'RequireCommittedFragment')
    if ($null -ne $match -and $requiresCommittedFragment) {
        $reply = Get-JsonPropertyValue -Object $match -Name 'reply'
        $fragment = Get-JsonPropertyValue -Object $reply -Name 'fragment'
        $fragmentId = Get-JsonPropertyValue -Object $fragment -Name 'id'
        if ($null -eq $fragmentId -or [int]$fragmentId -le 0) {
            $match = $null
        }
    }

    if ($null -eq $match) {
        $summary.Add("FAIL: $($item.Name)")
        $missing.Add($item.Name)
    } else {
        $matchArgs = Get-JsonPropertyValue -Object $match -Name 'args'
        $suffix = ''
        if ($requiresCommittedFragment) {
            $reply = Get-JsonPropertyValue -Object $match -Name 'reply'
            $fragment = Get-JsonPropertyValue -Object $reply -Name 'fragment'
            $suffix = " committedFragmentId=$([string](Get-JsonPropertyValue -Object $fragment -Name 'id'))"
        }
        $summary.Add("PASS: $($item.Name) correlationId=$([string](Get-JsonPropertyValue -Object $match -Name 'correlationId')) imageIdState=$([string](Get-JsonPropertyValue -Object $matchArgs -Name 'imageIdState'))$suffix")
    }
}

if ($missing.Count -gt 0) {
    $summary.Add('')
    $summary.Add('Missing required representative pairs:')
    foreach ($name in $missing) { $summary.Add("- $name") }
    $summaryText = $summary -join [Environment]::NewLine
    Write-Host $summaryText
    throw 'RPC diagnostic evidence is incomplete; nothing was copied into the Step 13 run.'
}

$destination = Join-Path $runDirectory $OutputName
Copy-Item -LiteralPath $source -Destination $destination -Force
$summary.Add('')
$summary.Add('PASS: no forbidden authentication/password keys or raw text field found')
$summary.Add("Copied validated diagnostic JSON to: $destination")

$summaryPath = Join-Path $runDirectory 'rpc-diagnostics-validation.txt'
Write-Utf8NoBom -Path $summaryPath -Text (($summary -join [Environment]::NewLine) + [Environment]::NewLine)

Write-Host ($summary -join [Environment]::NewLine)
Write-Host "Validation summary: $summaryPath"
