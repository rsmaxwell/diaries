param(
    [Parameter(Mandatory = $true)]
    [switch]$ProductionWriteFreezeConfirmed,

    [string]$SharedFilesRoot,
    [string]$SnapshotParent,
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
$EvidenceFile = Join-Path $EvidenceDirectory "shared-files-snapshot-$Timestamp.txt"

function Write-Evidence {
    param([string]$Message = '')
    $Message | Tee-Object -FilePath $EvidenceFile -Append
}

function Read-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Environment file does not exist: $Path" }
    $values = @{}
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = [string]$raw
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('#')) { continue }
        $equals = $line.IndexOf('=')
        if ($equals -lt 1) { continue }
        $values[$line.Substring(0, $equals).Trim()] = $line.Substring($equals + 1).Trim()
    }
    return $values
}

function Merge-DotEnv {
    param([hashtable]$Base, [hashtable]$Override)
    $result = @{}
    foreach ($key in $Base.Keys) { $result[$key] = $Base[$key] }
    foreach ($key in $Override.Keys) { $result[$key] = $Override[$key] }
    return $result
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

function Assert-LocalWriteFreeze {
    $known = @('diaries-local-responder', 'diaries-published-smoke-responder')
    $running = @(& docker ps --format '{{.Names}}' 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'docker ps failed while checking the local write freeze.' }
    foreach ($container in $known) {
        if ($running -contains $container) { throw "Local responder '$container' is running. Re-run freeze-local-writes.bat." }
    }
    $listeners = @(Get-TcpListeners -Port 8081)
    if ($listeners.Count -gt 0) { throw 'TCP/8081 is listening locally. Re-run freeze-local-writes.bat and stop the direct responder.' }
}

function Get-Inventory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$OutputFile
    )

    $rootPath = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
    $files = @(Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File | Sort-Object FullName)
    $totalBytes = [int64]0
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $writer = New-Object System.IO.StreamWriter($OutputFile, $false, $utf8NoBom)
    try {
        $writer.WriteLine("sha256`tbytes`trelativePath")
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($rootPath.Length).TrimStart('\').Replace('\','/')
            $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $totalBytes += [int64]$file.Length
            $writer.WriteLine("$hash`t$($file.Length)`t$relative")
        }
    } finally {
        $writer.Dispose()
    }
    return [pscustomobject]@{ Count = $files.Count; Bytes = $totalBytes }
}

if (-not $ProductionWriteFreezeConfirmed) {
    throw 'Production write freeze confirmation is required. Run the deployed production step8-freeze-writes.sh first, then rerun with -ProductionWriteFreezeConfirmed.'
}
Assert-LocalWriteFreeze

if ([string]::IsNullOrWhiteSpace($SharedFilesRoot)) {
    $modeEnv = Read-DotEnv (Join-Path $ProjectDir 'config\environments\local-docker-build.env')
    $localEnv = Read-DotEnv (Join-Path $ProjectDir 'config\environments\local.env')
    $effective = Merge-DotEnv $modeEnv $localEnv
    foreach ($key in 'DIARIES_NAS_HOST','DIARIES_NAS_SHARE','DIARIES_NAS_CONTENT_PATH') {
        if (-not $effective.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$effective[$key])) { throw "$key is required to infer the shared Files root." }
    }
    $content = ([string]$effective['DIARIES_NAS_CONTENT_PATH']).Replace('/', '\').Trim('\')
    $SharedFilesRoot = "\\$($effective['DIARIES_NAS_HOST'])\$($effective['DIARIES_NAS_SHARE'])\$content\files"
}
$SharedFilesRoot = $SharedFilesRoot.TrimEnd('\')
if (-not (Test-Path -LiteralPath $SharedFilesRoot -PathType Container)) { throw "Shared pre-migration Files root does not exist or is not accessible: $SharedFilesRoot" }

if ([string]::IsNullOrWhiteSpace($SnapshotParent)) {
    $contentRoot = Split-Path -Parent $SharedFilesRoot
    $SnapshotParent = Join-Path $contentRoot ".0031-backups\step8-$Timestamp"
}
$SnapshotParent = $SnapshotParent.TrimEnd('\')
$SnapshotRoot = Join-Path $SnapshotParent 'files'
if (Test-Path -LiteralPath $SnapshotParent) { throw "Snapshot destination already exists; refusing to merge/overwrite: $SnapshotParent" }
New-Item -ItemType Directory -Path $SnapshotParent -Force | Out-Null

$StagingReport = Join-Path $SnapshotParent 'STAGING-REVIEW.tsv'
$SourceInventory = Join-Path $SnapshotParent 'SOURCE-SHA256.tsv'
$SnapshotInventory = Join-Path $SnapshotParent 'SNAPSHOT-SHA256.tsv'
$SnapshotManifest = Join-Path $SnapshotParent 'SNAPSHOT-MANIFEST.json'

Write-Evidence '0031-FEAT Step 8 - shared pre-migration Files snapshot'
Write-Evidence "Captured: $(Get-Date -Format o)"
Write-Evidence "Source: $SharedFilesRoot"
Write-Evidence "Destination: $SnapshotRoot"
Write-Evidence 'Local write freeze: verified by container/port checks.'
Write-Evidence 'Production write freeze: explicitly confirmed by operator switch.'
Write-Evidence

$stagingRoot = Join-Path $SharedFilesRoot '.image-staging'
$stagingEntries = @()
if (Test-Path -LiteralPath $stagingRoot -PathType Container) {
    $stagingFiles = @(Get-ChildItem -LiteralPath $stagingRoot -Recurse -Force -File | Sort-Object FullName)
    foreach ($file in $stagingFiles) {
        $relative = $file.FullName.Substring($stagingRoot.TrimEnd('\').Length).TrimStart('\').Replace('\','/')
        $stagingEntries += [pscustomobject]@{ RelativePath = $relative; Bytes = [int64]$file.Length; LastWriteTime = $file.LastWriteTime.ToString('o') }
    }
}
"relativePath`tbytes`tlastWriteTime" | Set-Content -LiteralPath $StagingReport -Encoding utf8
foreach ($entry in $stagingEntries) {
    "$($entry.RelativePath)`t$($entry.Bytes)`t$($entry.LastWriteTime)" | Add-Content -LiteralPath $StagingReport -Encoding utf8
}
Write-Evidence "Staging files found: $($stagingEntries.Count)"
if ($stagingEntries.Count -gt 0) {
    Write-Evidence 'NOTICE: .image-staging is non-empty. The exact staging bytes will be retained in this rollback snapshot, but Step 10 must review them before seeding new dataset roots.'
} else {
    Write-Evidence 'Staging review: .image-staging is absent or contains no files.'
}

Write-Evidence 'Generating SHA-256 inventory of frozen source tree...'
$sourceSummary = Get-Inventory -Root $SharedFilesRoot -OutputFile $SourceInventory
Write-Evidence "Source file count: $($sourceSummary.Count)"
Write-Evidence "Source total bytes: $($sourceSummary.Bytes)"

New-Item -ItemType Directory -Path $SnapshotRoot -Force | Out-Null
$roboLog = Join-Path $SnapshotParent 'ROBOCOPY.log'
$roboArgs = @(
    $SharedFilesRoot,
    $SnapshotRoot,
    '/E', '/COPY:DAT', '/DCOPY:DAT', '/R:2', '/W:2', '/XJ', '/NP', '/TEE', "/LOG:$roboLog"
)
Write-Evidence 'Copying frozen shared Files tree with robocopy...'
& robocopy @roboArgs | Out-Null
$roboExit = $LASTEXITCODE
if ($roboExit -ge 8) { throw "robocopy failed with exit code $roboExit. See $roboLog" }
Write-Evidence "robocopy exit code: $roboExit (success is < 8)"

Write-Evidence 'Generating SHA-256 inventory of snapshot tree...'
$snapshotSummary = Get-Inventory -Root $SnapshotRoot -OutputFile $SnapshotInventory
if ($sourceSummary.Count -ne $snapshotSummary.Count -or $sourceSummary.Bytes -ne $snapshotSummary.Bytes) {
    throw 'Snapshot file count/byte total differs from the frozen source tree.'
}

$sourceLines = Get-Content -LiteralPath $SourceInventory
$snapshotLines = Get-Content -LiteralPath $SnapshotInventory
$diff = @(Compare-Object -ReferenceObject $sourceLines -DifferenceObject $snapshotLines -SyncWindow 0)
if ($diff.Count -ne 0) { throw "Snapshot SHA-256 inventory differs from source ($($diff.Count) differences)." }

$sourceInventoryHash = (Get-FileHash -LiteralPath $SourceInventory -Algorithm SHA256).Hash.ToLowerInvariant()
$snapshotInventoryHash = (Get-FileHash -LiteralPath $SnapshotInventory -Algorithm SHA256).Hash.ToLowerInvariant()
$stagingReportHash = (Get-FileHash -LiteralPath $StagingReport -Algorithm SHA256).Hash.ToLowerInvariant()

$gitCommit = 'unknown'
try {
    $candidate = (& git -C $ProjectDir rev-parse HEAD 2>$null | Select-Object -First 1)
    if (-not [string]::IsNullOrWhiteSpace($candidate)) { $gitCommit = $candidate.Trim() }
} catch { }

$manifest = [ordered]@{
    schemaVersion = 1
    captureType = '0031-step8-shared-files-premigration-snapshot'
    createdAt = (Get-Date).ToString('o')
    sourceFilesDir = 'files'
    sourceRoot = $SharedFilesRoot
    snapshotRoot = $SnapshotRoot
    copyTool = 'robocopy /E /COPY:DAT /DCOPY:DAT /XJ'
    sourceFileCount = $sourceSummary.Count
    sourceTotalBytes = $sourceSummary.Bytes
    snapshotFileCount = $snapshotSummary.Count
    snapshotTotalBytes = $snapshotSummary.Bytes
    sourceInventory = [ordered]@{ path = $SourceInventory; sha256 = $sourceInventoryHash }
    snapshotInventory = [ordered]@{ path = $SnapshotInventory; sha256 = $snapshotInventoryHash }
    inventoriesIdentical = $true
    staging = [ordered]@{
        path = '.image-staging'
        fileCount = $stagingEntries.Count
        reviewFile = $StagingReport
        reviewSha256 = $stagingReportHash
        includedInRollbackSnapshot = $true
        seedIntoNewRootsWithoutReview = $false
    }
    writeFreeze = [ordered]@{
        localVerified = $true
        productionConfirmedByOperator = $true
    }
    applicationSourceIdentity = [ordered]@{ gitCommit = $gitCommit }
    note = 'This is the exact rollback snapshot of the pre-split shared mutable Files tree. .image-staging is preserved for rollback only; Step 10 must decide explicitly whether any staging content belongs in newly seeded dataset roots.'
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($SnapshotManifest, (($manifest | ConvertTo-Json -Depth 10) + [Environment]::NewLine), $utf8NoBom)

$evidenceManifest = Join-Path $EvidenceDirectory "shared-files-snapshot-$Timestamp.json"
[System.IO.File]::WriteAllText($evidenceManifest, (($manifest | ConvertTo-Json -Depth 10) + [Environment]::NewLine), $utf8NoBom)

Write-Evidence
Write-Evidence 'PASS: source and snapshot SHA-256 inventories are identical.'
Write-Evidence "Files: $($sourceSummary.Count)"
Write-Evidence "Bytes: $($sourceSummary.Bytes)"
Write-Evidence "Source inventory SHA-256: $sourceInventoryHash"
Write-Evidence "Snapshot inventory SHA-256: $snapshotInventoryHash"
Write-Evidence "Snapshot manifest: $SnapshotManifest"
Write-Evidence "Repository evidence copy: $evidenceManifest"
Write-Evidence 'Do not restart production/local responders yet; Step 9 reconciliation is intended to run against the frozen pre-split state.'
