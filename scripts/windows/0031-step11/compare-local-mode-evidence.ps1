param(
    [string]$ProjectDir = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$ProjectDir = [System.IO.Path]::GetFullPath($ProjectDir)
$Runtime = Join-Path $ProjectDir 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 11\runtime'
$Modes = @('development-infrastructure','local-docker-build','local-published-smoke')
$reports = @()

foreach ($mode in $Modes) {
    $candidate = $null
    $directories = Get-ChildItem -LiteralPath $Runtime -Directory -Filter ($mode + '-*') -ErrorAction SilentlyContinue | Sort-Object Name -Descending
    foreach ($directory in $directories) {
        $path = Join-Path $directory.FullName 'STEP11-REPORT.json'
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $value = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
        if ($value.status -eq 'PASS') {
            $candidate = [pscustomobject]@{ Path=$path; Report=$value }
            break
        }
    }
    if ($null -eq $candidate) { throw "No passing Step 11 runtime report found for $mode." }
    $reports += $candidate
}

$selectors = @($reports | ForEach-Object { [string]$_.Report.filesSelector } | Select-Object -Unique)
$dbPaths = @($reports | ForEach-Object { ([string]$_.Report.effectiveDatabaseDataDir).TrimEnd([char[]]'\/').ToLowerInvariant() } | Select-Object -Unique)
$commonOverride = ($selectors.Count -eq 1 -and $selectors[0] -eq 'files-development-common')
if ($commonOverride -and $dbPaths.Count -ne 1) {
    throw 'Common local Files selector is active, but the three modes did not resolve to one database data directory.'
}
if ($commonOverride) {
    Write-Host 'PASS: all three local modes resolve the common database + files-development-common pair.'
} else {
    $expected = @{
        'development-infrastructure'='files-development-infrastructure'
        'local-docker-build'='files-local-docker-build'
        'local-published-smoke'='files-local-published-smoke'
    }
    foreach ($candidate in $reports) {
        $mode = [string]$candidate.Report.mode
        if ([string]$candidate.Report.filesSelector -ne $expected[$mode]) {
            throw "Unexpected isolated Files selector for ${mode}: $($candidate.Report.filesSelector)"
        }
    }
    Write-Host 'PASS: the three local modes resolve their approved isolated default database/Files pairs.'
}

foreach ($candidate in $reports) {
    if ([string]$candidate.Report.publicFilesContext -ne '/files') { throw "Public Files route changed for $($candidate.Report.mode)." }
    if (-not [bool]$candidate.Report.responderLogCaptured) { throw "Responder startup log is missing for $($candidate.Report.mode)." }
}
Write-Host 'PASS: every runtime report retains /files and includes responder startup/runtime logs.'

$summary = [ordered]@{
    feature='0031-FEAT'; step=11; generatedAt=(Get-Date).ToString('o'); status='PASS';
    commonOverride=$commonOverride;
    modes=@($reports | ForEach-Object {
        [ordered]@{
            mode=$_.Report.mode; databaseDataDir=$_.Report.effectiveDatabaseDataDir;
            filesSelector=$_.Report.filesSelector; filesBacking=$_.Report.filesBacking;
            report=$_.Path
        }
    })
}
$summaryPath = Join-Path (Split-Path $Runtime -Parent) 'STEP11-RUNTIME-SUMMARY.json'
$summary | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
Write-Host "PASS: Step 11 cross-mode summary written to $summaryPath"
