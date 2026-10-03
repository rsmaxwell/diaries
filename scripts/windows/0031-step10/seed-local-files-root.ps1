param(
    [ValidateSet('development-infrastructure', 'local-docker-build', 'local-published-smoke')]
    [string]$Mode = 'local-docker-build',

    [Parameter(Mandatory = $true)]
    [switch]$ProductionWriteFreezeConfirmed,

    [string]$SharedFilesRoot,
    [string]$TargetFilesRoot,
    [string]$Step8SnapshotParent,
    [string]$EvidenceDirectory
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir '..\..\..'))
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if ([string]::IsNullOrWhiteSpace($EvidenceDirectory)) {
    $EvidenceDirectory = Join-Path $ProjectDir "change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 10\runtime\$Timestamp"
}
$EvidenceDirectory = [System.IO.Path]::GetFullPath($EvidenceDirectory)
New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
$ConsoleEvidence = Join-Path $EvidenceDirectory 'STEP10-CONSOLE.txt'

function Write-Evidence {
    param([string]$Message = '')
    $Message | Tee-Object -FilePath $ConsoleEvidence -Append
}

function Read-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Environment file does not exist: $Path"
    }
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
        if ($running -contains $container) {
            throw "Local responder '$container' is running. Keep the Step 8 write freeze in force before seeding a new Files root."
        }
    }
    $listeners = @(Get-TcpListeners -Port 8081)
    if ($listeners.Count -gt 0) {
        throw 'TCP/8081 is listening locally. Stop the direct responder and keep the Step 8 write freeze in force.'
    }
}

function Get-RelativePathForInventory {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$FilePath
    )
    return $FilePath.Substring($RootPath.Length).TrimStart('\').Replace('\','/')
}

function Get-Inventory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$OutputFile,
        [switch]$ExcludeImageStaging
    )

    $rootPath = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
    $files = @(
        Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File |
            Sort-Object FullName
    )

    $included = New-Object System.Collections.Generic.List[object]
    foreach ($file in $files) {
        $relative = Get-RelativePathForInventory -RootPath $rootPath -FilePath $file.FullName
        if ($ExcludeImageStaging -and ($relative -eq '.image-staging' -or $relative.StartsWith('.image-staging/'))) {
            continue
        }
        $included.Add([pscustomobject]@{ File = $file; RelativePath = $relative })
    }

    $totalBytes = [int64]0
    $writer = New-Object System.IO.StreamWriter($OutputFile, $false, $Utf8NoBom)
    try {
        $writer.WriteLine("sha256`tbytes`trelativePath")
        foreach ($item in $included) {
            $hash = (Get-FileHash -LiteralPath $item.File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $totalBytes += [int64]$item.File.Length
            $writer.WriteLine("$hash`t$($item.File.Length)`t$($item.RelativePath)")
        }
    } finally {
        $writer.Dispose()
    }
    return [pscustomobject]@{ Count = $included.Count; Bytes = $totalBytes }
}

function Write-AclEvidence {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$OutputFile
    )
    $acl = Get-Acl -LiteralPath $Path
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("Path: $Path")
    $lines.Add("Owner: $($acl.Owner)")
    $lines.Add("AreAccessRulesProtected: $($acl.AreAccessRulesProtected)")
    $lines.Add("SDDL: $($acl.Sddl)")
    $lines.Add('')
    $lines.Add('Access rules:')
    foreach ($rule in @($acl.Access | Sort-Object IdentityReference, FileSystemRights, AccessControlType)) {
        $lines.Add("$($rule.IdentityReference)`t$($rule.AccessControlType)`t$($rule.FileSystemRights)`tInherited=$($rule.IsInherited)`tInheritance=$($rule.InheritanceFlags)`tPropagation=$($rule.PropagationFlags)")
    }
    [System.IO.File]::WriteAllLines($OutputFile, $lines, $Utf8NoBom)
}

function Write-JsonNoBom {
    param([Parameter(Mandatory = $true)]$Value, [Parameter(Mandatory = $true)][string]$Path)
    [System.IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 8) + [Environment]::NewLine, $Utf8NoBom)
}

if (-not $ProductionWriteFreezeConfirmed) {
    throw 'Production write freeze confirmation is required because the source Files tree is still the production Files root. Keep the deployed Step 8 production freeze in force and rerun with -ProductionWriteFreezeConfirmed.'
}
Assert-LocalWriteFreeze

$modeEnvPath = Join-Path $ProjectDir "config\environments\$Mode.env"
$modeEnv = Read-DotEnv $modeEnvPath
$localEnvPath = Join-Path $ProjectDir 'config\environments\local.env'
$localEnv = @{}
if (Test-Path -LiteralPath $localEnvPath -PathType Leaf) {
    $localEnv = Read-DotEnv $localEnvPath
}
$effective = Merge-DotEnv $modeEnv $localEnv

foreach ($key in 'DIARIES_DB_DATA_DIR','DIARIES_FILES_DIR') {
    if (-not $effective.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$effective[$key])) {
        throw "$key is required in the effective $Mode configuration."
    }
}

$dbDataDir = ([string]$effective['DIARIES_DB_DATA_DIR']).Replace('\','/').TrimEnd('/')
$dbLeaf = Split-Path -Leaf $dbDataDir
$filesDir = [string]$effective['DIARIES_FILES_DIR']
$approvedPairs = @{
    'development-infrastructure' = 'files-development-infrastructure'
    'local-docker-build' = 'files-local-docker-build'
    'local-published-smoke' = 'files-local-published-smoke'
    'common' = 'files-development-common'
}
if (-not $approvedPairs.ContainsKey($dbLeaf)) {
    throw "Effective database dataset '$dbDataDir' is not one of the frozen 0031 local datasets. Refusing to infer a Files root."
}
$expectedFilesDir = $approvedPairs[$dbLeaf]
if ($filesDir -ne $expectedFilesDir) {
    throw "Dataset/Files mismatch: database leaf '$dbLeaf' requires DIARIES_FILES_DIR=$expectedFilesDir, but effective configuration selects '$filesDir'."
}
if ($filesDir -eq 'files') {
    throw 'A local/non-production dataset must not seed or select the production Files root named files.'
}
if ($filesDir.IndexOfAny([System.IO.Path]::GetInvalidFileNameChars()) -ge 0 -or $filesDir.Contains('/') -or $filesDir.Contains('\')) {
    throw "DIARIES_FILES_DIR must be a leaf directory name, not a path: $filesDir"
}

# Use the Docker NAS environment as the physical content-root locator even when
# Mode=development-infrastructure. local.env still wins for any machine-local NAS override.
$nasBase = Read-DotEnv (Join-Path $ProjectDir 'config\environments\local-docker-build.env')
$nasEffective = Merge-DotEnv $nasBase $localEnv
foreach ($key in 'DIARIES_NAS_HOST','DIARIES_NAS_SHARE','DIARIES_NAS_CONTENT_PATH') {
    if (-not $nasEffective.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$nasEffective[$key])) {
        throw "$key is required to infer the NAS content root."
    }
}
$content = ([string]$nasEffective['DIARIES_NAS_CONTENT_PATH']).Replace('/', '\').Trim('\')
$contentRoot = "\\$($nasEffective['DIARIES_NAS_HOST'])\$($nasEffective['DIARIES_NAS_SHARE'])\$content"

if ([string]::IsNullOrWhiteSpace($SharedFilesRoot)) {
    $SharedFilesRoot = Join-Path $contentRoot 'files'
}
if ([string]::IsNullOrWhiteSpace($TargetFilesRoot)) {
    $TargetFilesRoot = Join-Path $contentRoot $filesDir
}
$SharedFilesRoot = [System.IO.Path]::GetFullPath($SharedFilesRoot).TrimEnd('\')
$TargetFilesRoot = [System.IO.Path]::GetFullPath($TargetFilesRoot).TrimEnd('\')

if (-not (Test-Path -LiteralPath $SharedFilesRoot -PathType Container)) {
    throw "Frozen shared source Files root does not exist or is not accessible: $SharedFilesRoot"
}
if ((Split-Path -Leaf $TargetFilesRoot) -ne $filesDir) {
    throw "Target Files root leaf must be the effective DIARIES_FILES_DIR '$filesDir': $TargetFilesRoot"
}
if ($SharedFilesRoot -eq $TargetFilesRoot) {
    throw 'Source and target Files roots resolve to the same path.'
}
if (Test-Path -LiteralPath $TargetFilesRoot) {
    throw "Target Files root already exists; refusing to merge or overwrite an existing dataset root: $TargetFilesRoot"
}

if ([string]::IsNullOrWhiteSpace($Step8SnapshotParent)) {
    $backupRoot = Join-Path (Split-Path -Parent $SharedFilesRoot) '.0031-backups'
    if (-not (Test-Path -LiteralPath $backupRoot -PathType Container)) {
        throw "Step 8 backup root not found: $backupRoot"
    }
    $candidates = @(
        Get-ChildItem -LiteralPath $backupRoot -Directory -Filter 'step8-*' |
            Where-Object {
                (Test-Path -LiteralPath (Join-Path $_.FullName 'SOURCE-SHA256.tsv') -PathType Leaf) -and
                (Test-Path -LiteralPath (Join-Path $_.FullName 'SNAPSHOT-MANIFEST.json') -PathType Leaf)
            } |
            Sort-Object Name -Descending
    )
    if ($candidates.Count -eq 0) {
        throw "No Step 8 snapshot with SOURCE-SHA256.tsv and SNAPSHOT-MANIFEST.json was found under $backupRoot"
    }
    $Step8SnapshotParent = $candidates[0].FullName
}
$Step8SnapshotParent = [System.IO.Path]::GetFullPath($Step8SnapshotParent).TrimEnd('\')
$step8SourceInventory = Join-Path $Step8SnapshotParent 'SOURCE-SHA256.tsv'
$step8Manifest = Join-Path $Step8SnapshotParent 'SNAPSHOT-MANIFEST.json'
if (-not (Test-Path -LiteralPath $step8SourceInventory -PathType Leaf) -or -not (Test-Path -LiteralPath $step8Manifest -PathType Leaf)) {
    throw "Step 8 snapshot evidence is incomplete: $Step8SnapshotParent"
}

$stagingRoot = Join-Path $SharedFilesRoot '.image-staging'
$stagingFiles = @()
if (Test-Path -LiteralPath $stagingRoot -PathType Container) {
    $stagingFiles = @(Get-ChildItem -LiteralPath $stagingRoot -Recurse -Force -File | Sort-Object FullName)
}
if ($stagingFiles.Count -gt 1) {
    throw "Step 9 disposition approved only the zero-byte catalogue.lock, but $($stagingFiles.Count) staging files now exist. Reconcile/review again before Step 10."
}
if ($stagingFiles.Count -eq 1) {
    $stagingFile = $stagingFiles[0]
    $relativeStaging = $stagingFile.FullName.Substring($stagingRoot.TrimEnd('\').Length).TrimStart('\').Replace('\','/')
    $hash = (Get-FileHash -LiteralPath $stagingFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($relativeStaging -ne 'catalogue.lock' -or $stagingFile.Length -ne 0 -or $hash -ne 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855') {
        throw "Current .image-staging content no longer matches the reviewed Step 9 catalogue.lock disposition. Reconcile/review again before Step 10."
    }
}

$SourceFullInventory = Join-Path $EvidenceDirectory 'SOURCE-FULL-SHA256.tsv'
$SourceSeedInventory = Join-Path $EvidenceDirectory 'SOURCE-SEED-SHA256.tsv'
$TargetInventory = Join-Path $EvidenceDirectory 'TARGET-SHA256.tsv'
$StagingInventory = Join-Path $EvidenceDirectory 'EXCLUDED-STAGING-SHA256.tsv'
$SourceAcl = Join-Path $EvidenceDirectory 'SOURCE-ACL.txt'
$TargetAcl = Join-Path $EvidenceDirectory 'TARGET-ACL.txt'
$RoboLog = Join-Path $EvidenceDirectory 'ROBOCOPY.log'

Write-Evidence '0031-FEAT Step 10 - seed independent non-production Files root'
Write-Evidence "Captured: $(Get-Date -Format o)"
Write-Evidence "Mode used to resolve effective dataset: $Mode"
Write-Evidence "Effective database dataset: $dbDataDir"
Write-Evidence "Effective DIARIES_FILES_DIR: $filesDir"
Write-Evidence "Source shared Files root: $SharedFilesRoot"
Write-Evidence "Target candidate Files root: $TargetFilesRoot"
Write-Evidence "Step 8 source baseline: $Step8SnapshotParent"
Write-Evidence 'Local write freeze: verified by container/port checks.'
Write-Evidence 'Production write freeze: explicitly confirmed by operator switch.'
Write-Evidence

Write-Evidence 'Generating full SHA-256 inventory of the frozen source tree...'
$sourceFullSummary = Get-Inventory -Root $SharedFilesRoot -OutputFile $SourceFullInventory
$baselineLines = Get-Content -LiteralPath $step8SourceInventory
$currentLines = Get-Content -LiteralPath $SourceFullInventory
$baselineDiff = @(Compare-Object -ReferenceObject $baselineLines -DifferenceObject $currentLines -SyncWindow 0)
if ($baselineDiff.Count -ne 0) {
    throw "Frozen shared source no longer matches the Step 8 SOURCE-SHA256.tsv baseline ($($baselineDiff.Count) differences). Do not seed Step 10 from a changed source."
}
Write-Evidence "Source matches Step 8 baseline exactly: $($sourceFullSummary.Count) files, $($sourceFullSummary.Bytes) bytes."

Write-Evidence 'Generating approved seed inventory (entire source except .image-staging)...'
$sourceSeedSummary = Get-Inventory -Root $SharedFilesRoot -OutputFile $SourceSeedInventory -ExcludeImageStaging
Write-Evidence "Approved seed inventory: $($sourceSeedSummary.Count) files, $($sourceSeedSummary.Bytes) bytes."

"sha256`tbytes`trelativePath" | Set-Content -LiteralPath $StagingInventory -Encoding utf8
foreach ($file in $stagingFiles) {
    $relative = $file.FullName.Substring($SharedFilesRoot.Length).TrimStart('\').Replace('\','/')
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash`t$($file.Length)`t$relative" | Add-Content -LiteralPath $StagingInventory -Encoding utf8
}
Write-Evidence "Excluded .image-staging file count: $($stagingFiles.Count)."
if ($stagingFiles.Count -eq 1) {
    Write-Evidence 'Excluded staging entry is the reviewed zero-byte .image-staging/catalogue.lock from Step 9.'
} else {
    Write-Evidence 'No staging file is present; the .image-staging directory is still excluded from the new dataset seed.'
}

Write-AclEvidence -Path $SharedFilesRoot -OutputFile $SourceAcl

$targetParent = Split-Path -Parent $TargetFilesRoot
$tempLeaf = ".0031-step10-seed-$filesDir-$Timestamp"
$tempRoot = Join-Path $targetParent $tempLeaf
if (Test-Path -LiteralPath $tempRoot) {
    throw "Temporary seed path unexpectedly exists: $tempRoot"
}
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

$roboArgs = @(
    $SharedFilesRoot,
    $tempRoot,
    '/E', '/COPY:DAT', '/DCOPY:DAT', '/R:2', '/W:2', '/XJ', '/NP', '/TEE',
    '/XD', (Join-Path $SharedFilesRoot '.image-staging'),
    "/LOG:$RoboLog"
)
Write-Evidence "Copying approved source content into temporary seed root: $tempRoot"
& robocopy @roboArgs | Out-Null
$roboExit = $LASTEXITCODE
if ($roboExit -ge 8) {
    throw "robocopy failed with exit code $roboExit. Partial seed remains at $tempRoot for inspection; see $RoboLog"
}
Write-Evidence "robocopy exit code: $roboExit (success is < 8)."

$TempInventory = Join-Path $EvidenceDirectory 'TEMP-TARGET-SHA256.tsv'
$tempSummary = Get-Inventory -Root $tempRoot -OutputFile $TempInventory
if ($sourceSeedSummary.Count -ne $tempSummary.Count -or $sourceSeedSummary.Bytes -ne $tempSummary.Bytes) {
    throw "Temporary seed count/byte total differs from approved source seed inventory. Partial seed remains at $tempRoot."
}
$seedLines = Get-Content -LiteralPath $SourceSeedInventory
$tempLines = Get-Content -LiteralPath $TempInventory
$tempDiff = @(Compare-Object -ReferenceObject $seedLines -DifferenceObject $tempLines -SyncWindow 0)
if ($tempDiff.Count -ne 0) {
    throw "Temporary seed SHA-256 inventory differs from approved source seed inventory ($($tempDiff.Count) differences). Partial seed remains at $tempRoot."
}
Write-Evidence 'Temporary seed SHA-256 inventory matches the approved source seed inventory exactly.'

# Promote only after the complete byte-for-byte seed has been verified. Because the
# rename stays within one parent directory, the final candidate does not become
# visible under its configured name until verification has succeeded.
Rename-Item -LiteralPath $tempRoot -NewName (Split-Path -Leaf $TargetFilesRoot)
if (-not (Test-Path -LiteralPath $TargetFilesRoot -PathType Container)) {
    throw "Verified temporary seed could not be promoted to the final target: $TargetFilesRoot"
}

$targetSummary = Get-Inventory -Root $TargetFilesRoot -OutputFile $TargetInventory
$targetLines = Get-Content -LiteralPath $TargetInventory
$targetDiff = @(Compare-Object -ReferenceObject $seedLines -DifferenceObject $targetLines -SyncWindow 0)
if ($targetDiff.Count -ne 0 -or $sourceSeedSummary.Count -ne $targetSummary.Count -or $sourceSeedSummary.Bytes -ne $targetSummary.Bytes) {
    throw 'Final target inventory changed during promotion; keep responders frozen and inspect the target before continuing.'
}

# Non-destructive-after-cleanup permission probe. It verifies that the account used
# for local migration can create, write, read, and remove a file in the candidate
# root. Step 11 still verifies the actual responder runtime mount separately.
$probe = Join-Path $TargetFilesRoot ".0031-step10-write-probe-$Timestamp.tmp"
$probePayload = "0031 Step 10 permission probe $Timestamp"
try {
    [System.IO.File]::WriteAllText($probe, $probePayload, $Utf8NoBom)
    $readBack = [System.IO.File]::ReadAllText($probe, $Utf8NoBom)
    if ($readBack -ne $probePayload) { throw 'Permission probe read-back did not match written content.' }
} finally {
    if (Test-Path -LiteralPath $probe -PathType Leaf) { Remove-Item -LiteralPath $probe -Force }
}
if (Test-Path -LiteralPath $probe) { throw "Permission probe could not be removed: $probe" }
Write-Evidence 'Target create/write/read/delete permission probe: PASS.'
Write-AclEvidence -Path $TargetFilesRoot -OutputFile $TargetAcl
Write-Evidence "Source and target ACL/SDDL captures written for operator review: $(Split-Path -Leaf $SourceAcl), $(Split-Path -Leaf $TargetAcl)."

# The probe must leave the verified inventory unchanged.
$PostProbeInventory = Join-Path $EvidenceDirectory 'TARGET-POST-PROBE-SHA256.tsv'
$postProbeSummary = Get-Inventory -Root $TargetFilesRoot -OutputFile $PostProbeInventory
$postProbeLines = Get-Content -LiteralPath $PostProbeInventory
$postProbeDiff = @(Compare-Object -ReferenceObject $seedLines -DifferenceObject $postProbeLines -SyncWindow 0)
if ($postProbeDiff.Count -ne 0 -or $postProbeSummary.Count -ne $sourceSeedSummary.Count -or $postProbeSummary.Bytes -ne $sourceSeedSummary.Bytes) {
    throw 'Permission probe did not leave the candidate Files root byte-for-byte equal to the approved seed inventory.'
}

$report = [ordered]@{
    schemaVersion = 1
    feature = '0031-FEAT'
    step = 10
    status = 'CANDIDATE_ROOT_CREATED'
    createdAt = (Get-Date).ToString('o')
    mode = $Mode
    dataset = [ordered]@{
        databaseDataDir = $dbDataDir
        databaseLeaf = $dbLeaf
        filesDir = $filesDir
    }
    source = [ordered]@{
        root = $SharedFilesRoot
        step8SnapshotParent = $Step8SnapshotParent
        fullFileCount = $sourceFullSummary.Count
        fullTotalBytes = $sourceFullSummary.Bytes
        matchesStep8SourceInventory = $true
        approvedSeedFileCount = $sourceSeedSummary.Count
        approvedSeedTotalBytes = $sourceSeedSummary.Bytes
    }
    staging = [ordered]@{
        sourcePath = $stagingRoot
        excludedFromSeed = $true
        fileCount = $stagingFiles.Count
        disposition = 'Step 9 reviewed transient/control state; do not blindly propagate'
    }
    target = [ordered]@{
        root = $TargetFilesRoot
        fileCount = $postProbeSummary.Count
        totalBytes = $postProbeSummary.Bytes
        exactApprovedSeedInventoryMatch = $true
        writeReadDeleteProbe = 'PASS'
        aclEvidence = $TargetAcl
    }
    copy = [ordered]@{
        tool = 'robocopy /E /COPY:DAT /DCOPY:DAT /XJ with .image-staging excluded'
        robocopyExitCode = $roboExit
        usedVerifiedTemporaryRootBeforePromotion = $true
    }
    writeFreeze = [ordered]@{
        local = 'verified'
        production = 'operator-confirmed'
    }
    operatorReview = [ordered]@{
        aclReviewRequiredBeforeStep10CloseOut = $true
        note = 'Review SOURCE-ACL.txt and TARGET-ACL.txt/NAS permissions. Step 11 separately verifies the responder runtime can read the candidate while writes remain frozen.'
    }
}
$reportPath = Join-Path $EvidenceDirectory 'STEP10-REPORT.json'
Write-JsonNoBom -Value $report -Path $reportPath

$markdown = @"
# 0031-FEAT Step 10 — candidate Files root report

- Effective database dataset: $dbDataDir
- Effective Files selector: $filesDir
- Frozen source: $SharedFilesRoot
- Candidate target: $TargetFilesRoot
- Source matches Step 8 baseline: **yes**
- Approved seed inventory: **$($sourceSeedSummary.Count) files / $($sourceSeedSummary.Bytes) bytes**
- Final target inventory: **$($postProbeSummary.Count) files / $($postProbeSummary.Bytes) bytes**
- Exact SHA-256 inventory match: **yes**
- `.image-staging`: **excluded by reviewed Step 9 disposition**
- Target create/write/read/delete probe: **PASS**
- Original shared `files` tree: **not deleted or modified by this script**
- Step 8 rollback snapshot: **not deleted or modified by this script**

The candidate root is ready for Step 10 permission/ACL review and then Step 11
configuration cut-over. Both responder write paths must remain frozen.
"@
[System.IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'STEP10-REPORT.md'), $markdown + [Environment]::NewLine, $Utf8NoBom)

Write-Evidence
Write-Evidence 'Step 10 candidate Files root created and byte-for-byte verified.'
Write-Evidence "  Dataset:                  $dbDataDir"
Write-Evidence "  Files selector:           $filesDir"
Write-Evidence "  Candidate root:           $TargetFilesRoot"
Write-Evidence "  Files copied:             $($postProbeSummary.Count)"
Write-Evidence "  Bytes copied:             $($postProbeSummary.Bytes)"
Write-Evidence '  .image-staging propagated: no'
Write-Evidence '  Permission probe:         PASS'
Write-Evidence "  Evidence directory:       $EvidenceDirectory"
Write-Evidence 'RESULT: CANDIDATE ROOT READY. Review SOURCE-ACL.txt and TARGET-ACL.txt before closing Step 10. Keep both responder write paths frozen.'
