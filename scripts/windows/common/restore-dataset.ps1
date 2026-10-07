param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('development-infrastructure', 'local-docker-build', 'local-published-smoke')]
    [string]$ModeName,

    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [Parameter(Mandatory = $true)]
    [string]$BackupInput,

    [switch]$PreflightOnly,

    [switch]$PrepareOnly,

    [switch]$ApplyOnly,

    [switch]$RollbackOnly,

    [switch]$PostflightOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$SupportedModes = @('development-infrastructure', 'local-docker-build', 'local-published-smoke')
$DatabaseKey = 'DIARIES_DB_DATA_DIR'
$FilesKey = 'DIARIES_FILES_DIR'
$StagingName = '.image-staging'
$DirectResponderMain = 'com.rsmaxwell.diaries.responder.Responder'
$PotentialDirectWriterMains = @(
    'com.rsmaxwell.diaries.responder.migration.migration0024.Migration0024ImageCatalogue',
    'com.rsmaxwell.diaries.responder.migration.migration0022.Migration0022Inventory'
)

function Read-DotEnvFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Environment file does not exist: $Path" }
    $values = @{}
    $present = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($rawLine in Get-Content -LiteralPath $Path) {
        $line = [string]$rawLine
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('#')) { continue }
        $equals = $line.IndexOf('=')
        if ($equals -lt 1) { continue }
        $key = $line.Substring(0, $equals).Trim()
        $value = $line.Substring($equals + 1).Trim()
        if ([string]::IsNullOrWhiteSpace($key)) { continue }
        $values[$key] = $value
        [void]$present.Add($key)
    }
    [pscustomobject]@{ Values = $values; Present = $present }
}

function Import-DotEnvValues {
    param([Parameter(Mandatory = $true)][hashtable]$Values)
    foreach ($key in $Values.Keys) { [Environment]::SetEnvironmentVariable([string]$key, [string]$Values[$key], 'Process') }
}

function Get-ModeEnvironmentFile {
    param([Parameter(Mandatory = $true)][string]$Mode)
    Join-Path $script:ProjectPath "config\environments\$Mode.env"
}

function Get-ModeSelection {
    param([Parameter(Mandatory = $true)][string]$Mode)
    $modeFile = Get-ModeEnvironmentFile -Mode $Mode
    $modeEnv = Read-DotEnvFile -Path $modeFile
    $localEnv = Read-DotEnvFile -Path $script:LocalEnvironmentFile
    if (-not $modeEnv.Values.ContainsKey($DatabaseKey) -or -not $modeEnv.Values.ContainsKey($FilesKey)) {
        throw "$modeFile must define $DatabaseKey and $FilesKey."
    }
    $dbOverride = $localEnv.Present.Contains($DatabaseKey)
    $filesOverride = $localEnv.Present.Contains($FilesKey)
    if ($dbOverride -xor $filesOverride) { throw "Dataset override mismatch in $($script:LocalEnvironmentFile): $DatabaseKey and $FilesKey must be overridden together." }
    $database = if ($dbOverride) { [string]$localEnv.Values[$DatabaseKey] } else { [string]$modeEnv.Values[$DatabaseKey] }
    $files = if ($filesOverride) { [string]$localEnv.Values[$FilesKey] } else { [string]$modeEnv.Values[$FilesKey] }
    $databasePath = if ([System.IO.Path]::IsPathRooted($database)) { [System.IO.Path]::GetFullPath($database) } else { [System.IO.Path]::GetFullPath((Join-Path $script:ProjectPath $database)) }
    [pscustomobject]@{ Mode = $Mode; DatabaseDataDir = $database; DatabasePath = $databasePath; DatasetName = Split-Path -Leaf $databasePath; FilesDir = $files }
}

function Invoke-DatasetPairValidation {
    $validator = Join-Path $script:ProjectPath 'scripts\windows\common\validate-dataset-pair.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $validator -ModeName $ModeName -ModeEnvironmentFile $script:ModeEnvironmentFile -LocalEnvironmentFile $script:LocalEnvironmentFile
    if ($LASTEXITCODE -ne 0) { throw "Existing dataset-pair validation failed for $ModeName." }
}

function Resolve-EffectiveDataset {
    $resolver = Join-Path $script:ProjectPath 'scripts\windows\common\resolve-effective-dataset.ps1'
    $records = & $resolver -ModeName $ModeName -ProjectDir $script:ProjectPath -DatabaseDataDir $env:DIARIES_DB_DATA_DIR -FilesDir $env:DIARIES_FILES_DIR
    $resolved = @{}
    foreach ($record in $records) {
        $line = [string]$record; $equals = $line.IndexOf('=')
        if ($equals -gt 0) { $resolved[$line.Substring(0, $equals)] = $line.Substring($equals + 1) }
    }
    foreach ($required in 'DIARIES_DATASET_NAME','DIARIES_EFFECTIVE_DB_DATA_DIR','DIARIES_EFFECTIVE_FILES_ROOT','DIARIES_DATASET_SHARING') {
        if (-not $resolved.ContainsKey($required) -or [string]::IsNullOrWhiteSpace([string]$resolved[$required])) { throw "Effective dataset resolver did not return $required." }
    }
    $resolved
}

function Get-ComposeFile { param([string]$Mode) Join-Path $script:ProjectPath "compose.$Mode.yaml" }
function Get-ComposeArguments {
    param([Parameter(Mandatory = $true)][string]$Mode)
    @('compose', '--env-file', (Get-ModeEnvironmentFile -Mode $Mode), '--env-file', $script:LocalEnvironmentFile, '-f', (Get-ComposeFile -Mode $Mode))
}


function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    # Windows PowerShell 5.1 converts native stderr redirected with 2>&1 into
    # ErrorRecord objects. With this script's ErrorActionPreference=Stop, even a
    # benign stderr line from a successful command (for example SLF4J(I)) can
    # become a terminating NativeCommandError before LASTEXITCODE is inspected.
    # Temporarily make native stderr non-terminating, capture both streams, then
    # use the native process exit code as the authoritative success criterion.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $FilePath @Arguments 2>&1)
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    return [pscustomobject]@{ ExitCode = [int]$code; Output = @($output) }
}

function Invoke-Docker {
    param([Parameter(Mandatory = $true)][string[]]$Arguments, [switch]$CaptureOutput, [switch]$AllowFailure)
    if ($CaptureOutput) {
        # docker logs deliberately preserves the container's stdout/stderr split.
        # Under Windows PowerShell 5.1, redirecting native stderr with 2>&1 while
        # ErrorActionPreference=Stop can turn harmless container stderr (for
        # example SLF4J informational startup lines) into a terminating
        # NativeCommandError before LASTEXITCODE can be inspected. Reuse the
        # native-capture helper so docker's process exit code remains the
        # authoritative success criterion.
        $result = Invoke-NativeCapture -FilePath 'docker.exe' -Arguments $Arguments
        if (-not $AllowFailure -and $result.ExitCode -ne 0) {
            throw "docker command failed with exit code $($result.ExitCode): docker $($Arguments -join ' ')`n$($result.Output -join [Environment]::NewLine)"
        }
        return $result
    }
    & docker.exe @Arguments; $code = $LASTEXITCODE
    if (-not $AllowFailure -and $code -ne 0) { throw "docker command failed with exit code ${code}: docker $($Arguments -join ' ')" }
    return $code
}

function Get-ComposeServiceContainerId {
    param([string]$Mode, [string]$Service)
    $result = Invoke-Docker -Arguments ((Get-ComposeArguments -Mode $Mode) + @('ps','-q',$Service)) -CaptureOutput -AllowFailure
    if ($result.ExitCode -ne 0) { return $null }
    foreach ($line in $result.Output) { $value = ([string]$line).Trim(); if ($value) { return $value } }
    return $null
}
function Test-ContainerRunning {
    param([string]$ContainerId)
    $result = Invoke-Docker -Arguments @('inspect','--format','{{.State.Running}}',$ContainerId) -CaptureOutput -AllowFailure
    return ($result.ExitCode -eq 0 -and (([string]($result.Output | Select-Object -First 1)).Trim().ToLowerInvariant() -eq 'true'))
}
function Test-DockerResponderRunning {
    param([string]$Mode)
    $id = Get-ComposeServiceContainerId -Mode $Mode -Service 'diaries-responder'
    return (-not [string]::IsNullOrWhiteSpace($id)) -and (Test-ContainerRunning -ContainerId $id)
}
function Stop-DockerResponder {
    param([string]$Mode)
    [void](Invoke-Docker -Arguments ((Get-ComposeArguments -Mode $Mode) + @('stop','diaries-responder')))
}

function Get-DirectWriterProcesses {
    try { $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'java.exe'" -ErrorAction Stop) }
    catch { throw "Unable to inspect local Java writer processes through Win32_Process: $($_.Exception.Message)" }
    $knownResponder = @(); $unknownPotential = @()
    foreach ($process in $processes) {
        $command = [string]$process.CommandLine
        if ([string]::IsNullOrWhiteSpace($command)) { continue }
        if ($command.Contains($DirectResponderMain)) { $knownResponder += $process; continue }
        foreach ($main in $PotentialDirectWriterMains) { if ($command.Contains($main)) { $unknownPotential += $process; break } }
    }
    [pscustomobject]@{ Responders = @($knownResponder); PotentialWriters = @($unknownPotential) }
}

function Wait-ForWriterStop {
    param([int]$Seconds = 20)
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $running = @()
        foreach ($mode in $script:KnownConsumers) { if ($mode -ne 'development-infrastructure' -and (Test-DockerResponderRunning -Mode $mode)) { $running += "docker:$mode/diaries-responder" } }
        if ($script:KnownConsumers -contains 'development-infrastructure') {
            $direct = Get-DirectWriterProcesses
            foreach ($p in $direct.Responders) { $running += "windows:PID-$($p.ProcessId)" }
            foreach ($p in $direct.PotentialWriters) { $running += "windows:potential-writer-PID-$($p.ProcessId)" }
        }
        if ($running.Count -eq 0) { return }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Writer quiescence could not be proved; still running: $($running -join ', ')"
}

function Get-StagingInspection {
    param([Parameter(Mandatory = $true)][string]$FilesRoot)
    $stagingPath = Join-Path $FilesRoot $StagingName
    $entries = @(); $disposition = 'empty'; $note = 'target .image-staging absent or empty; transient staging is outside durable restore content'
    if (Test-Path -LiteralPath $stagingPath) {
        if (-not (Test-Path -LiteralPath $stagingPath -PathType Container)) { throw "$StagingName exists but is not a directory: $stagingPath" }
        $stagingDirectory = Get-Item -LiteralPath $stagingPath -Force -ErrorAction Stop
        $entries = @(Get-ChildItem -LiteralPath $stagingPath -Force -Recurse -ErrorAction Stop)
        if ($entries.Count -eq 1) {
            $entry = $entries[0]
            if ((-not $entry.PSIsContainer) -and $entry.Name -eq 'catalogue.lock' -and $entry.Directory.FullName -eq $stagingDirectory.FullName -and [int64]$entry.Length -eq 0) {
                $disposition = 'excluded-benign'; $note = 'target .image-staging contains only expected zero-byte catalogue.lock; transient staging remains outside restore payload'
            }
        }
        if (-not (($entries.Count -eq 0) -or $disposition -eq 'excluded-benign')) {
            $sample = @($entries | Select-Object -First 5 | ForEach-Object { $_.FullName }) -join '; '
            throw "Refusing complete restore preparation: target $StagingName contains $($entries.Count) unexplained entries. Only empty or the expected zero-byte catalogue.lock is permitted. Sample: $sample"
        }
    }
    [pscustomobject]@{ Path = $stagingPath; EntryCount = $entries.Count; Disposition = $disposition; Note = $note }
}

function Invoke-PythonScript {
    param([Parameter(Mandatory = $true)][string]$ScriptPath, [Parameter(Mandatory = $true)][string[]]$Arguments)
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) { throw "Python helper not found: $ScriptPath" }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue; $prefix = @()
    if ($null -eq $python) { $python = Get-Command py.exe -ErrorAction SilentlyContinue; if ($null -ne $python) { $prefix = @('-3') } }
    if ($null -eq $python) { throw 'Python 3 is required for complete-dataset restore validation.' }
    $output = & $python.Source @prefix $ScriptPath @Arguments 2>&1; $code = $LASTEXITCODE
    if ($code -ne 0) { throw "Python helper failed with exit code ${code}: $ScriptPath $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)" }
    foreach ($line in $output) { Write-Host ([string]$line) }
}

function Normalize-IdentityPath {
    param([Parameter(Mandatory = $true)][string]$PathValue, [switch]$RelativeToProject)
    $value = $PathValue.Trim().Replace('/', '\')
    if ($RelativeToProject -and -not [System.IO.Path]::IsPathRooted($value)) { $value = Join-Path $script:ProjectPath $value }
    try { if ([System.IO.Path]::IsPathRooted($value)) { $value = [System.IO.Path]::GetFullPath($value) } } catch { }
    return $value.TrimEnd('\').ToLowerInvariant()
}

function Resolve-BackupDirectory {
    param([Parameter(Mandatory = $true)][string]$InputValue, [Parameter(Mandatory = $true)][string]$DatasetName)
    $candidate = $InputValue.Trim('"')
    if (Test-Path -LiteralPath $candidate) {
        $item = Get-Item -LiteralPath $candidate -Force
        if (-not $item.PSIsContainer) {
            $lower = $item.Name.ToLowerInvariant()
            if ($lower.EndsWith('.dataset.json') -or $lower.EndsWith('.dump') -or $lower.EndsWith('.sql')) {
                throw 'Complete restore requires a completed complete-backup directory. DATABASE-ONLY dump/SQL/.dataset.json inputs are not accepted.'
            }
            throw "Complete restore input must be a backup directory, not a file: $($item.FullName)"
        }
        return $item.FullName
    }
    if ($candidate -match '^\d{8}-\d{6}Z$') {
        $path = Join-Path (Join-Path (Join-Path $script:ProjectPath 'data\dataset-backups') $DatasetName) $candidate
        if (Test-Path -LiteralPath $path -PathType Container) { return [System.IO.Path]::GetFullPath($path) }
        throw "Completed complete backup not found for dataset '$DatasetName': $path"
    }
    throw "Complete backup directory or backup ID not found: $InputValue"
}

function Read-Manifest {
    param([string]$BackupDir)
    $path = Join-Path $BackupDir 'dataset-manifest.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $databaseOnly = @(Get-ChildItem -LiteralPath $BackupDir -Filter '*.dataset.json' -File -ErrorAction SilentlyContinue)
        if ($databaseOnly.Count -gt 0) { throw 'Selected directory contains DATABASE-ONLY .dataset.json metadata but no dataset-manifest.json; it is not a complete restore input.' }
        throw "Complete backup manifest is missing: $path"
    }
    try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { throw "Complete backup manifest is not readable JSON: $path ($($_.Exception.Message))" }
}

function Assert-ManifestMatchesTarget {
    param([object]$Manifest, [string]$DatasetName, [string]$DatabaseIdentity, [string]$FilesSelector, [string]$FilesRoot)
    if ([int]$Manifest.schemaVersion -ne 2 -or [string]$Manifest.backupType -ne 'complete-dataset' -or -not [bool]$Manifest.completeDatasetBackup -or [string]$Manifest.status -ne 'complete') {
        throw 'Restore input is not a completed schema-2 complete-dataset backup.'
    }
    if ([string]$Manifest.logicalDataset -ne $DatasetName) { throw "Backup logical dataset '$($Manifest.logicalDataset)' does not match target '$DatasetName'." }
    if ([string]$Manifest.database.name -ne $env:DIARIES_DB_NAME) { throw "Backup database '$($Manifest.database.name)' does not match target '$($env:DIARIES_DB_NAME)'." }
    if ((Normalize-IdentityPath -PathValue ([string]$Manifest.database.storageIdentity) -RelativeToProject) -ne (Normalize-IdentityPath -PathValue $DatabaseIdentity -RelativeToProject)) {
        throw 'Backup database storage identity does not match the current effective target database.'
    }
    if ([string]$Manifest.files.selector -ne $FilesSelector) { throw "Backup Files selector '$($Manifest.files.selector)' does not match target '$FilesSelector'." }
    if ((Normalize-IdentityPath -PathValue ([string]$Manifest.files.resolvedPhysicalRoot) -RelativeToProject) -ne (Normalize-IdentityPath -PathValue $FilesRoot -RelativeToProject)) {
        throw 'Backup resolved Files root identity does not match the current effective target Files root.'
    }
}

function Test-CustomDumpWithPgRestore {
    param([string]$BackupDir, [string]$ContainerId)
    $dump = Join-Path $BackupDir 'database\diaries.dump'
    $containerPath = "/tmp/diaries-0033-restore-preflight-$([Guid]::NewGuid().ToString('N')).dump"
    try {
        [void](Invoke-Docker -Arguments @('cp',$dump,"${ContainerId}:${containerPath}"))
        $result = Invoke-Docker -Arguments @('exec',$ContainerId,'pg_restore','--list',$containerPath) -CaptureOutput
        if ($result.Output.Count -eq 0) { throw 'pg_restore --list returned no archive catalogue output.' }
    }
    finally { try { [void](Invoke-Docker -Arguments @('exec',$ContainerId,'rm','-f',$containerPath) -AllowFailure) } catch { } }
}

function Get-DurableTargetBytes {
    param([string]$FilesRoot)
    $stagingPath = Join-Path $FilesRoot $StagingName
    $total = [int64]0
    foreach ($file in @(Get-ChildItem -LiteralPath $FilesRoot -File -Recurse -Force -ErrorAction Stop)) {
        if ($file.FullName.StartsWith($stagingPath + '\', [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        $total += [int64]$file.Length
    }
    return $total
}

function Get-LocalFreeBytes {
    param([string]$PathValue)
    try {
        $full = [System.IO.Path]::GetFullPath($PathValue)
        if ($full.StartsWith('\\')) { return $null }
        $root = [System.IO.Path]::GetPathRoot($full)
        if ([string]::IsNullOrWhiteSpace($root)) { return $null }
        return [int64]([System.IO.DriveInfo]::new($root).AvailableFreeSpace)
    }
    catch { return $null }
}

function Get-WriterState {
    $dockerStates = @()
    foreach ($consumer in $script:KnownConsumers) {
        if ($consumer -eq 'development-infrastructure') { continue }
        $dockerStates += [ordered]@{ mode = $consumer; service = 'diaries-responder'; wasRunning = (Test-DockerResponderRunning -Mode $consumer); stoppedByRestorePreparation = $false }
    }
    $directState = [ordered]@{ applicable = ($script:KnownConsumers -contains 'development-infrastructure'); wasRunning = $false; processIds = @(); stoppedByRestorePreparation = $false; restartCommand = 'diaries-responder\scripts\windows\run-responder.bat' }
    if ($directState.applicable) {
        $direct = Get-DirectWriterProcesses
        if ($direct.PotentialWriters.Count -gt 0) {
            $description = @($direct.PotentialWriters | ForEach-Object { "PID=$($_.ProcessId) $($_.CommandLine)" }) -join [Environment]::NewLine
            throw "A migration/maintenance Java process may be writing the selected dataset. Stop it before restore preparation:`n$description"
        }
        $directState.wasRunning = ($direct.Responders.Count -gt 0)
        $directState.processIds = @($direct.Responders | ForEach-Object { [int]$_.ProcessId })
    }
    [pscustomobject]@{ DockerResponders = @($dockerStates); DirectResponder = $directState }
}

function Stop-Writers {
    param([object]$WriterState)
    foreach ($writer in $WriterState.DockerResponders) {
        if ([bool]$writer.wasRunning) { Stop-DockerResponder -Mode ([string]$writer.mode); $writer.stoppedByRestorePreparation = $true }
    }
    if ($WriterState.DirectResponder.applicable -and [bool]$WriterState.DirectResponder.wasRunning) {
        foreach ($pidValue in $WriterState.DirectResponder.processIds) { Stop-Process -Id ([int]$pidValue) -ErrorAction Stop }
        $WriterState.DirectResponder.stoppedByRestorePreparation = $true
    }
    Wait-ForWriterStop
}

function Write-RestoreState {
    param([object]$State, [string]$WorkDir)
    New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
    $path = Join-Path $WorkDir 'restore-state.json'
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, (($State | ConvertTo-Json -Depth 14) + [Environment]::NewLine), $utf8NoBom)
}


function Read-RestoreState {
    param([Parameter(Mandatory = $true)][string]$PreparedDir)
    $path = Join-Path $PreparedDir 'restore-state.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Prepared restore state is missing: $path" }
    try { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { throw "Prepared restore state is not readable JSON: $path ($($_.Exception.Message))" }
}

function Assert-PreparedStateMatchesCurrentTarget {
    param([object]$State, [string]$SourceBackupId, [string]$BackupDir, [string]$DatasetName, [string]$DatabaseIdentity, [string]$FilesSelector, [string]$FilesRoot)
    if ([int]$State.schemaVersion -ne 1 -or [string]$State.feature -ne '0033-FEAT') { throw 'Prepared restore state has an unsupported schema/feature identity.' }
    if ([string]$State.restoreSource.backupId -ne $SourceBackupId) { throw 'Prepared restore state backup ID does not match the selected complete backup.' }
    if ((Normalize-IdentityPath -PathValue ([string]$State.restoreSource.directory) -RelativeToProject) -ne (Normalize-IdentityPath -PathValue $BackupDir -RelativeToProject)) { throw 'Prepared restore state backup directory does not match the selected complete backup.' }
    if ([string]$State.target.logicalDataset -ne $DatasetName) { throw 'Prepared restore state logical dataset no longer matches the effective target.' }
    if ((Normalize-IdentityPath -PathValue ([string]$State.target.databaseStorageIdentity) -RelativeToProject) -ne (Normalize-IdentityPath -PathValue $DatabaseIdentity -RelativeToProject)) { throw 'Prepared restore state database identity no longer matches the effective target.' }
    if ([string]$State.target.filesSelector -ne $FilesSelector) { throw 'Prepared restore state Files selector no longer matches the effective target.' }
    if ((Normalize-IdentityPath -PathValue ([string]$State.target.resolvedFilesRoot) -RelativeToProject) -ne (Normalize-IdentityPath -PathValue $FilesRoot -RelativeToProject)) { throw 'Prepared restore state Files root no longer matches the effective target.' }
    if (-not [bool]$State.safetyBackup.required -or -not [bool]$State.safetyBackup.verified -or [string]::IsNullOrWhiteSpace([string]$State.safetyBackup.directory)) { throw 'Prepared restore state does not contain a verified mandatory safety backup.' }
    if (-not [bool]$State.stagedFiles.copied -or -not [bool]$State.stagedFiles.inventoryVerified) { throw 'Prepared restore state does not contain a verified staged replacement Files tree.' }
    if (-not [bool]$State.priorWriters.quiesced) { throw 'Prepared restore state does not prove writer quiescence.' }
}

function Ensure-Step6StateFields {
    param([object]$State, [string]$SourceBackupId, [string]$FilesRoot)
    if ($null -eq $State.PSObject.Properties['apply']) {
        $filesParent = Split-Path -Parent $FilesRoot; $filesLeaf = Split-Path -Leaf $FilesRoot
        $rollbackDir = Join-Path $filesParent ".$filesLeaf.pre-restore-$SourceBackupId.rollback"
        $apply = [ordered]@{
            confirmation = [ordered]@{ requiredToken = 'APPLY'; received = $false; at = $null }
            startedAt = $null; completedAt = $null
            database = [ordered]@{ beforeOid = $null; beforeImageRowCount = $null; dropStarted = $false; dropComplete = $false; createComplete = $false; restoreComplete = $false; afterOid = $null; afterImageRowCount = $null }
            files = [ordered]@{ rollbackDirectory = $rollbackDir; liveMovedToRollback = $false; replacementPromoted = $false; inventoryVerified = $false; runtimeStagingRecreated = $false; fileCount = $null; totalBytes = $null }
        }
        $State | Add-Member -NotePropertyName apply -NotePropertyValue $apply -Force
    }
    if ($null -eq $State.PSObject.Properties['rollback']) {
        $rollback = [ordered]@{ command = "restore-dataset.bat rollback $SourceBackupId"; safetyBackupId = [string]$State.safetyBackup.backupId; safetyBackupDirectory = [string]$State.safetyBackup.directory; filesDirectory = [string]$State.apply.files.rollbackDirectory; startedAt = $null; completedAt = $null; failedReplacementDirectory = $null; status = 'available' }
        $State | Add-Member -NotePropertyName rollback -NotePropertyValue $rollback -Force
    }
}

function Get-DatabaseSnapshot {
    param([Parameter(Mandatory = $true)][string]$ContainerId)
    $dbNameSql = $env:DIARIES_DB_NAME.Replace("'", "''")
    $oidResult = Invoke-Docker -Arguments @('exec',$ContainerId,'psql','--no-psqlrc','-At','--username',$env:DIARIES_DB_USERNAME,'--dbname','postgres','--set','ON_ERROR_STOP=1','--command',"SELECT oid FROM pg_database WHERE datname = '$dbNameSql';") -CaptureOutput
    $oidText = ([string]($oidResult.Output | Select-Object -First 1)).Trim()
    if ($oidText -notmatch '^\d+$') { throw "Could not determine PostgreSQL database OID for $($env:DIARIES_DB_NAME): $oidText" }
    $countResult = Invoke-Docker -Arguments @('exec',$ContainerId,'psql','--no-psqlrc','-At','--username',$env:DIARIES_DB_USERNAME,'--dbname',$env:DIARIES_DB_NAME,'--set','ON_ERROR_STOP=1','--command','SELECT count(*) FROM public.image;') -CaptureOutput
    $countText = ([string]($countResult.Output | Select-Object -First 1)).Trim()
    if ($countText -notmatch '^\d+$') { throw "Could not determine Image row count from restored database: $countText" }
    [pscustomobject]@{ Oid = [int64]$oidText; ImageRowCount = [int64]$countText }
}

function Invoke-DatabaseRestoreFromCompleteBackup {
    param([Parameter(Mandatory = $true)][string]$BackupDir, [Parameter(Mandatory = $true)][string]$ContainerId, [Parameter(Mandatory = $true)][object]$State, [Parameter(Mandatory = $true)][object]$Progress, [Parameter(Mandatory = $true)][string]$StateDir)
    $dump = Join-Path $BackupDir 'database\diaries.dump'
    $containerPath = "/tmp/diaries-0033-restore-apply-$([Guid]::NewGuid().ToString('N')).dump"
    try {
        [void](Invoke-Docker -Arguments @('cp',$dump,"${ContainerId}:${containerPath}"))
        $list = Invoke-Docker -Arguments @('exec',$ContainerId,'pg_restore','--list',$containerPath) -CaptureOutput
        if ($list.Output.Count -eq 0) { throw 'pg_restore --list returned no archive catalogue output immediately before destructive database restore.' }

        $Progress.dropStarted = $true
        $State.status = 'step6-dropping-database'; Write-RestoreState -State $State -WorkDir $StateDir
        [void](Invoke-Docker -Arguments @('exec',$ContainerId,'dropdb','--force','--if-exists','--username',$env:DIARIES_DB_USERNAME,$env:DIARIES_DB_NAME))
        $Progress.dropComplete = $true; $State.liveDataset.databaseChanged = $true
        $State.status = 'step6-creating-database'; Write-RestoreState -State $State -WorkDir $StateDir
        [void](Invoke-Docker -Arguments @('exec',$ContainerId,'createdb','--username',$env:DIARIES_DB_USERNAME,'--owner',$env:DIARIES_DB_USERNAME,$env:DIARIES_DB_NAME))
        $Progress.createComplete = $true
        $State.status = 'step6-restoring-database'; Write-RestoreState -State $State -WorkDir $StateDir
        [void](Invoke-Docker -Arguments @('exec',$ContainerId,'pg_restore','--exit-on-error','--no-owner','--no-privileges','--username',$env:DIARIES_DB_USERNAME,'--dbname',$env:DIARIES_DB_NAME,$containerPath))
        $Progress.restoreComplete = $true; Write-RestoreState -State $State -WorkDir $StateDir
    }
    finally { try { [void](Invoke-Docker -Arguments @('exec',$ContainerId,'rm','-f',$containerPath) -AllowFailure) } catch { } }
}


function Move-DirectorySameParent {
    param([Parameter(Mandatory = $true)][string]$Source, [Parameter(Mandatory = $true)][string]$Destination)
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) { throw "Directory rename source does not exist: $Source" }
    if (Test-Path -LiteralPath $Destination) { throw "Directory rename destination already exists: $Destination" }
    $sourceParent = (Split-Path -Parent ([System.IO.Path]::GetFullPath($Source))).TrimEnd('\')
    $destinationParent = (Split-Path -Parent ([System.IO.Path]::GetFullPath($Destination))).TrimEnd('\')
    if (-not [string]::Equals($sourceParent,$destinationParent,[System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing non-same-parent Files move: '$Source' -> '$Destination'. Step 6 requires rename/swap semantics on one filesystem."
    }
    [System.IO.Directory]::Move($Source,$Destination)
}

function Invoke-FilesApplySwap {
    param([object]$State, [string]$StateDir, [string]$BackupDir, [string]$FilesRoot, [string]$StagePath)
    $rollbackPath = [string]$State.apply.files.rollbackDirectory
    if (Test-Path -LiteralPath $rollbackPath) { throw "Rollback Files directory already exists; refusing to overwrite recovery state: $rollbackPath" }
    if (-not (Test-Path -LiteralPath $StagePath -PathType Container)) { throw "Verified Step-5 replacement stage is missing: $StagePath" }
    if (-not (Test-Path -LiteralPath $FilesRoot -PathType Container)) { throw "Live Files root is missing before Step-6 swap: $FilesRoot" }

    $State.status = 'step6-moving-live-files-to-rollback'; Write-RestoreState -State $State -WorkDir $StateDir
    Move-DirectorySameParent -Source $FilesRoot -Destination $rollbackPath
    $State.apply.files.liveMovedToRollback = $true; $State.liveDataset.filesRootChanged = $true
    $State.status = 'step6-promoting-staged-files'; Write-RestoreState -State $State -WorkDir $StateDir
    try {
        Move-DirectorySameParent -Source $StagePath -Destination $FilesRoot
        $State.apply.files.replacementPromoted = $true; Write-RestoreState -State $State -WorkDir $StateDir
    }
    catch {
        $promotionMessage = $_.Exception.Message
        if (-not (Test-Path -LiteralPath $FilesRoot) -and (Test-Path -LiteralPath $rollbackPath -PathType Container)) {
            try {
                Move-DirectorySameParent -Source $rollbackPath -Destination $FilesRoot
                $State.apply.files.liveMovedToRollback = $false; $State.liveDataset.filesRootChanged = $false
                Write-RestoreState -State $State -WorkDir $StateDir
                throw "Staged Files promotion failed, but the original live Files root was automatically restored: $promotionMessage"
            }
            catch {
                if ($_.Exception.Message -like 'Staged Files promotion failed, but*') { throw }
                throw "Staged Files promotion failed and automatic restoration of the original live Files root also failed. Original rollback path: $rollbackPath. Promotion error: $promotionMessage. Rollback error: $($_.Exception.Message)"
            }
        }
        throw
    }

    $runtimeStaging = Join-Path $FilesRoot $StagingName
    if (Test-Path -LiteralPath $runtimeStaging) { throw "Restored durable Files unexpectedly contains $StagingName before runtime staging recreation: $runtimeStaging" }
    New-Item -ItemType Directory -Path $runtimeStaging -ErrorAction Stop | Out-Null
    $State.apply.files.runtimeStagingRecreated = $true; Write-RestoreState -State $State -WorkDir $StateDir
    Invoke-PythonScript -ScriptPath $script:StageHelper -Arguments @('--backup-dir',$BackupDir,'--staged-files-root',$FilesRoot,'--allow-benign-runtime-staging')
    $State.apply.files.inventoryVerified = $true
    $manifest = Read-Manifest -BackupDir $BackupDir
    $State.apply.files.fileCount = [int64]$manifest.files.snapshot.fileCount
    $State.apply.files.totalBytes = [int64]$manifest.files.snapshot.totalBytes
    Write-RestoreState -State $State -WorkDir $StateDir
}

function Invoke-FilesRollbackSwap {
    param([object]$State, [string]$StateDir, [string]$SafetyBackupDir, [string]$FilesRoot, [string]$SourceBackupId)
    $rollbackPath = [string]$State.rollback.filesDirectory
    if (-not (Test-Path -LiteralPath $rollbackPath -PathType Container)) {
        # Files application may never have started. Prove the still-live tree is the safety-backup tree.
        Invoke-PythonScript -ScriptPath $script:StageHelper -Arguments @('--backup-dir',$SafetyBackupDir,'--staged-files-root',$FilesRoot,'--allow-benign-runtime-staging')
        return
    }
    $filesParent = Split-Path -Parent $FilesRoot; $filesLeaf = Split-Path -Leaf $FilesRoot
    $failedPath = Join-Path $filesParent ".$filesLeaf.failed-restore-$SourceBackupId-$([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ'))"
    if (Test-Path -LiteralPath $failedPath) { throw "Rollback diagnostic Files directory already exists: $failedPath" }
    if (Test-Path -LiteralPath $FilesRoot -PathType Container) {
        Move-DirectorySameParent -Source $FilesRoot -Destination $failedPath
        $State.rollback.failedReplacementDirectory = $failedPath; Write-RestoreState -State $State -WorkDir $StateDir
    }
    try {
        Move-DirectorySameParent -Source $rollbackPath -Destination $FilesRoot
    }
    catch {
        if (-not (Test-Path -LiteralPath $FilesRoot) -and (Test-Path -LiteralPath $failedPath -PathType Container)) {
            try { Move-DirectorySameParent -Source $failedPath -Destination $FilesRoot; $State.rollback.failedReplacementDirectory = $null; Write-RestoreState -State $State -WorkDir $StateDir } catch { }
        }
        throw
    }
    Invoke-PythonScript -ScriptPath $script:StageHelper -Arguments @('--backup-dir',$SafetyBackupDir,'--staged-files-root',$FilesRoot,'--allow-benign-runtime-staging')
    $State.liveDataset.filesRootChanged = $false
    Write-RestoreState -State $State -WorkDir $StateDir
}

function New-SafetyBackupId {
    param([string]$DatasetName)
    $root = Join-Path (Join-Path $script:ProjectPath 'data\dataset-backups') $DatasetName
    for ($offset = 0; $offset -lt 120; $offset++) {
        $id = [DateTime]::UtcNow.AddSeconds($offset).ToString('yyyyMMdd-HHmmssZ')
        if (-not (Test-Path -LiteralPath (Join-Path $root $id)) -and -not (Test-Path -LiteralPath (Join-Path $root ".$id.partial"))) { return $id }
    }
    throw 'Unable to allocate a unique UTC backup ID for the pre-restore safety backup.'
}

function Invoke-SafetyBackup {
    param([string]$SafetyBackupId)
    $backupScript = Join-Path $script:ProjectPath 'scripts\windows\common\backup-dataset.ps1'
    Write-Host ''
    Write-Host "Creating mandatory pre-restore COMPLETE DATASET safety backup: $SafetyBackupId"

    # Native/child PowerShell output is pipeline data. Never let that output become
    # this function's return value: callers persist the safety-backup path into
    # restore-state.json, so accidental stdout capture would turn the path into an
    # array of console lines. Capture locally, replay through Write-Host, and derive
    # the authoritative path independently from the allocated backup ID.
    $backupOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $backupScript -ModeName $ModeName -ProjectDir $script:ProjectPath -BackupId $SafetyBackupId 2>&1
    $backupExitCode = $LASTEXITCODE
    foreach ($line in @($backupOutput)) { Write-Host ([string]$line) }
    if ($backupExitCode -ne 0) { throw "Pre-restore safety backup failed with exit code $backupExitCode. Writers remain stopped." }

    $path = Join-Path (Join-Path (Join-Path $script:ProjectPath 'data\dataset-backups') $script:DatasetName) $SafetyBackupId
    if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw "Safety backup command returned success but final backup directory is missing: $path" }
    Invoke-PythonScript -ScriptPath $script:ManifestHelper -Arguments @('verify','--backup-dir',$path)
}

function Copy-BackupFilesToStage {
    param([string]$BackupDir, [string]$StagePath)
    $source = Join-Path $BackupDir 'files'
    if (Test-Path -LiteralPath $StagePath) { throw "Restore staging path already exists; refusing to merge/reuse it: $StagePath" }
    New-Item -ItemType Directory -Path $StagePath -Force | Out-Null
    & robocopy.exe $source $StagePath /MIR /COPY:DAT /DCOPY:DAT /R:2 /W:1 /XJ /NFL /NDL /NP
    $code = $LASTEXITCODE
    if ($code -ge 8) { throw "robocopy failed with exit code $code while staging replacement Files." }
}



function Stop-AllKnownWriters {
    foreach ($mode in $script:KnownConsumers) {
        if ($mode -eq 'development-infrastructure') { continue }
        try { if (Test-DockerResponderRunning -Mode $mode) { Stop-DockerResponder -Mode $mode } } catch { }
    }
    if ($script:KnownConsumers -contains 'development-infrastructure') {
        try {
            $direct = Get-DirectWriterProcesses
            foreach ($process in $direct.Responders) { try { Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction Stop } catch { } }
        } catch { }
    }
    Wait-ForWriterStop
}

function Wait-ForContainerHealthy {
    param([Parameter(Mandatory = $true)][string]$ContainerId, [int]$Seconds = 90)
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $result = Invoke-Docker -Arguments @('inspect','--format','{{if .State.Health}}{{.State.Health.Status}}{{else}}{{if .State.Running}}running{{else}}stopped{{end}}{{end}}',$ContainerId) -CaptureOutput -AllowFailure
        if ($result.ExitCode -eq 0) {
            $status = ([string]($result.Output | Select-Object -First 1)).Trim().ToLowerInvariant()
            if ($status -eq 'healthy' -or $status -eq 'running') { return }
            if ($status -eq 'unhealthy' -or $status -eq 'stopped') { throw "Container did not become healthy/running: $ContainerId status=$status" }
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for container health: $ContainerId"
}

function Ensure-MqttInfrastructureRunning {
    param([Parameter(Mandatory = $true)][string]$Mode)
    $id = Get-ComposeServiceContainerId -Mode $Mode -Service 'diaries-mqtt'
    if ([string]::IsNullOrWhiteSpace($id) -or -not (Test-ContainerRunning -ContainerId $id)) {
        [void](Invoke-Docker -Arguments ((Get-ComposeArguments -Mode $Mode) + @('up','-d','diaries-mqtt')))
        $id = Get-ComposeServiceContainerId -Mode $Mode -Service 'diaries-mqtt'
    }
    if ([string]::IsNullOrWhiteSpace($id)) { throw "Could not resolve $Mode diaries-mqtt container for postflight." }
    Wait-ForContainerHealthy -ContainerId $id -Seconds 60
    return $id
}

function Get-PostflightResponderConfigPath {
    param([Parameter(Mandatory = $true)][string]$Mode)
    if ($Mode -eq 'development-infrastructure') {
        $prepare = Join-Path $script:ProjectPath 'scripts\windows\development-infrastructure\prepare-responder-config.bat'
        $prepareResult = Invoke-NativeCapture -FilePath $env:ComSpec -Arguments @('/d','/c',"call `"$prepare`"")
        if ($prepareResult.ExitCode -ne 0) { throw "Could not prepare effective development responder configuration:`n$($prepareResult.Output -join [Environment]::NewLine)" }
        foreach ($line in @($prepareResult.Output)) { Write-Host ([string]$line) }
        $path = Join-Path $script:ProjectPath 'build\development-infrastructure\responder.effective.json'
    } else {
        $raw = [string]$env:DIARIES_RESPONDER_DOCKER_CONFIG_FILE
        if ([string]::IsNullOrWhiteSpace($raw)) { throw "DIARIES_RESPONDER_DOCKER_CONFIG_FILE is required for $Mode postflight." }
        $raw = [Environment]::ExpandEnvironmentVariables($raw)
        $path = if ([System.IO.Path]::IsPathRooted($raw)) { $raw } else { Join-Path $script:ProjectPath $raw }
    }
    $path = [System.IO.Path]::GetFullPath($path)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Responder configuration not found for postflight: $path" }
    return $path
}

function Start-DirectPostflightResponder {
    param([Parameter(Mandatory = $true)][string]$PostflightDir)
    $config = Get-PostflightResponderConfigPath -Mode 'development-infrastructure'
    $gradle = Join-Path $script:ProjectPath 'gradlew.bat'
    Write-Host 'Preparing direct responder distribution for Step-7 startup/replay verification...'
    $gradleResult = Invoke-NativeCapture -FilePath $gradle -Arguments @(':diaries-responder:installDist','--no-daemon')
    foreach ($line in @($gradleResult.Output)) { Write-Host ([string]$line) }
    if ($gradleResult.ExitCode -ne 0) { throw "Gradle installDist failed while preparing Step-7 responder verification:`n$($gradleResult.Output -join [Environment]::NewLine)" }
    $launcher = Join-Path $script:ProjectPath 'diaries-responder\build\install\diaries-responder\bin\diaries-responder.bat'
    if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw "Responder launcher was not created: $launcher" }
    New-Item -ItemType Directory -Path $PostflightDir -Force | Out-Null
    $stdout = Join-Path $PostflightDir 'responder.stdout.log'; $stderr = Join-Path $PostflightDir 'responder.stderr.log'
    Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
    $command = "/d /c call `"$launcher`" --config `"$config`""
    $process = Start-Process -FilePath $env:ComSpec -ArgumentList $command -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    [pscustomobject]@{ Kind='direct'; Mode='development-infrastructure'; ConfigPath=$config; Process=$process; ContainerId=$null; Stdout=$stdout; Stderr=$stderr; StartedAt=[DateTime]::UtcNow; HttpPort=8081 }
}

function Start-DockerPostflightResponder {
    param([Parameter(Mandatory = $true)][string]$Mode, [Parameter(Mandatory = $true)][string]$PostflightDir)
    [void](Ensure-MqttInfrastructureRunning -Mode $Mode)
    $started = [DateTime]::UtcNow
    [void](Invoke-Docker -Arguments ((Get-ComposeArguments -Mode $Mode) + @('up','-d','--no-deps','diaries-responder')))
    $id = Get-ComposeServiceContainerId -Mode $Mode -Service 'diaries-responder'
    if ([string]::IsNullOrWhiteSpace($id)) { throw "Could not resolve $Mode responder container after start." }
    Wait-ForContainerHealthy -ContainerId $id -Seconds 120
    $config = Get-PostflightResponderConfigPath -Mode $Mode
    $port = 8081
    if ($Mode -eq 'local-docker-build' -and -not [string]::IsNullOrWhiteSpace($env:DIARIES_RESPONDER_PORT)) { $port = [int]$env:DIARIES_RESPONDER_PORT }
    if ($Mode -eq 'local-published-smoke' -and -not [string]::IsNullOrWhiteSpace($env:DIARIES_RESPONDER_HTTP_HOST_PORT)) { $port = [int]$env:DIARIES_RESPONDER_HTTP_HOST_PORT }
    [pscustomobject]@{ Kind='docker'; Mode=$Mode; ConfigPath=$config; Process=$null; ContainerId=$id; Stdout=$null; Stderr=$null; StartedAt=$started; HttpPort=$port }
}

function Start-PostflightProbeResponder {
    param([Parameter(Mandatory = $true)][string]$Mode, [Parameter(Mandatory = $true)][string]$PostflightDir)
    [void](Ensure-MqttInfrastructureRunning -Mode $Mode)
    if ($Mode -eq 'development-infrastructure') { return (Start-DirectPostflightResponder -PostflightDir $PostflightDir) }
    return (Start-DockerPostflightResponder -Mode $Mode -PostflightDir $PostflightDir)
}

function Stop-PostflightProbeResponder {
    param([object]$Probe)
    if ($null -eq $Probe) { return }
    if ([string]$Probe.Kind -eq 'docker') {
        try { if (Test-DockerResponderRunning -Mode ([string]$Probe.Mode)) { Stop-DockerResponder -Mode ([string]$Probe.Mode) } } catch { }
    } else {
        try {
            $direct = Get-DirectWriterProcesses
            foreach ($process in $direct.Responders) { try { Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction Stop } catch { } }
        } catch { }
    }
    Wait-ForWriterStop
}

function Invoke-DirectResponderHealthCheck {
    param([Parameter(Mandatory = $true)][string]$ConfigPath)
    $classpath = Join-Path $script:ProjectPath 'diaries-responder\build\install\diaries-responder\lib\*'
    $deadline = (Get-Date).AddSeconds(90); $last = @()
    do {
        $result = Invoke-NativeCapture -FilePath 'java.exe' -Arguments @('-cp',$classpath,'com.rsmaxwell.diaries.responder.health.ResponderHealthCheck','--config',$ConfigPath)
        $last = @($result.Output)
        if ($result.ExitCode -eq 0) { return }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "Direct responder MQTT RPC health check did not succeed:`n$($last -join [Environment]::NewLine)"
}

function Get-PostflightProbeLogs {
    param([Parameter(Mandatory = $true)][object]$Probe)
    if ([string]$Probe.Kind -eq 'docker') {
        $since = ([DateTime]$Probe.StartedAt).ToString('o')
        $result = Invoke-Docker -Arguments @('logs','--since',$since,[string]$Probe.ContainerId) -CaptureOutput -AllowFailure
        return @($result.Output) -join [Environment]::NewLine
    }
    Start-Sleep -Milliseconds 500
    $parts = @()
    foreach ($path in @([string]$Probe.Stdout,[string]$Probe.Stderr)) {
        if ($path -and (Test-Path -LiteralPath $path -PathType Leaf)) { $parts += (Get-Content -LiteralPath $path -Raw -ErrorAction SilentlyContinue) }
    }
    return $parts -join [Environment]::NewLine
}

function Export-ImageCatalogueJson {
    param([Parameter(Mandatory = $true)][string]$ContainerId, [Parameter(Mandatory = $true)][string]$OutputPath)
    $sql = "SELECT COALESCE(json_agg(json_build_object('id',id,'relativePath',relative_path,'checksum',checksum,'mimeType',mime_type) ORDER BY id),'[]'::json)::text FROM public.image;"
    $result = Invoke-Docker -Arguments @('exec',$ContainerId,'psql','--no-psqlrc','-At','--username',$env:DIARIES_DB_USERNAME,'--dbname',$env:DIARIES_DB_NAME,'--set','ON_ERROR_STOP=1','--command',$sql) -CaptureOutput
    $json = (@($result.Output) -join '').Trim()
    try { $rows = @($json | ConvertFrom-Json) } catch { throw "Could not parse restored Image catalogue JSON: $($_.Exception.Message)" }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($OutputPath, $json + [Environment]::NewLine, $utf8NoBom)
    return $rows
}

function Get-RepresentativeMarqueeId {
    param([Parameter(Mandatory = $true)][string]$ContainerId)
    $result = Invoke-Docker -Arguments @('exec',$ContainerId,'psql','--no-psqlrc','-At','--username',$env:DIARIES_DB_USERNAME,'--dbname',$env:DIARIES_DB_NAME,'--set','ON_ERROR_STOP=1','--command','SELECT id FROM public.marquee ORDER BY id LIMIT 1;') -CaptureOutput
    $text = ([string]($result.Output | Select-Object -First 1)).Trim()
    if ($text -notmatch '^\d+$') { throw 'Restored database contains no representative MARQUEE row for Step-7 verification.' }
    return [int64]$text
}

function Get-MqttRetainedPayload {
    param([Parameter(Mandatory = $true)][string]$BrokerContainerId, [Parameter(Mandatory = $true)][string]$ConfigPath, [Parameter(Mandatory = $true)][string]$Topic)
    $config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $username = [string]$config.mqtt.user.username; $password = [string]$config.mqtt.user.password
    if ([string]::IsNullOrWhiteSpace($username) -or [string]::IsNullOrWhiteSpace($password)) { throw 'Responder MQTT credentials are missing from effective configuration.' }
    $result = Invoke-NativeCapture -FilePath 'docker.exe' -Arguments @('exec',$BrokerContainerId,'mosquitto_sub','-h','localhost','-p','1883','-u',$username,'-P',$password,'-t',$Topic,'-C','1','-W','8')
    if ($result.ExitCode -ne 0) { throw "No retained MQTT payload was readable for $Topic during Step-7 postflight:`n$($result.Output -join [Environment]::NewLine)" }
    $payload = (@($result.Output) -join [Environment]::NewLine).Trim()
    if ([string]::IsNullOrWhiteSpace($payload)) { throw "Retained MQTT payload is empty for $Topic." }
    try { return $payload | ConvertFrom-Json } catch { throw "Retained MQTT payload is not valid JSON for ${Topic}: $($_.Exception.Message)" }
}

function Convert-ToUrlPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return (($RelativePath -split '/') | ForEach-Object { [Uri]::EscapeDataString($_) }) -join '/'
}

function Assert-RepresentativeHttpImage {
    param([Parameter(Mandatory = $true)][object]$Image, [Parameter(Mandatory = $true)][int]$Port, [Parameter(Mandatory = $true)][string]$PostflightDir)
    if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) { throw 'curl.exe is required for Step-7 /files verification.' }
    $relativePath = [string]$Image.relativePath; $expected = [string]$Image.checksum
    $url = "http://localhost:$Port/files/$(Convert-ToUrlPath -RelativePath $relativePath)"
    $download = Join-Path $PostflightDir 'representative-image.bin'
    & curl.exe --fail --silent --show-error --max-time 15 --output $download $url
    if ($LASTEXITCODE -ne 0) { throw "Representative Image was not readable through responder /files mapping: $url" }
    $actual = (Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Representative /files Image checksum mismatch for $relativePath" }
    return $url
}

function Restore-PriorWriterState {
    param([Parameter(Mandatory = $true)][object]$State, [Parameter(Mandatory = $true)][string]$PostflightDir)
    $started = @()
    foreach ($writer in @($State.priorWriters.dockerResponders)) {
        if (-not [bool]$writer.wasRunning) { continue }
        $mode = [string]$writer.mode
        [void](Ensure-MqttInfrastructureRunning -Mode $mode)
        [void](Invoke-Docker -Arguments ((Get-ComposeArguments -Mode $mode) + @('up','-d','--no-deps','diaries-responder')))
        $id = Get-ComposeServiceContainerId -Mode $mode -Service 'diaries-responder'
        if ([string]::IsNullOrWhiteSpace($id)) { throw "Could not restore prior responder state for $mode." }
        Wait-ForContainerHealthy -ContainerId $id -Seconds 120
        $started += "docker:$mode/diaries-responder"
    }
    if ([bool]$State.priorWriters.directResponder.wasRunning) {
        $probe = Start-DirectPostflightResponder -PostflightDir (Join-Path $PostflightDir 'restored-direct-writer')
        Invoke-DirectResponderHealthCheck -ConfigPath ([string]$probe.ConfigPath)
        $started += 'windows:direct-diaries-responder'
    }
    return @($started)
}

function Invoke-Step7Postflight {
    param([Parameter(Mandatory = $true)][object]$State, [Parameter(Mandatory = $true)][string]$StateDir, [Parameter(Mandatory = $true)][string]$BackupDir, [Parameter(Mandatory = $true)][object]$Manifest, [Parameter(Mandatory = $true)][string]$FilesRoot, [Parameter(Mandatory = $true)][string]$ContainerId)
    if ([string]$State.status -notin @('applied-awaiting-step7','step7-postflight-failed')) { throw "Restore state is not ready for Step 7 postflight; current status: $($State.status)" }
    Wait-ForWriterStop
    $postflightDir = Join-Path $StateDir 'postflight'; New-Item -ItemType Directory -Path $postflightDir -Force | Out-Null
    if ($null -eq $State.PSObject.Properties['postflight']) {
        $State | Add-Member -NotePropertyName postflight -NotePropertyValue ([ordered]@{
            startedAt=$null; completedAt=$null; status='pending'; databaseVerified=$false; filesInventoryVerified=$false;
            catalogueReconciliationVerified=$false; responderProbeMode=$ModeName; responderHealthVerified=$false; retainedReplayVerified=$false;
            representativeMarqueeId=$null; representativeImageId=$null; representativeImagePath=$null; representativeFilesUrl=$null;
            priorWriterStateRestored=$false; restoredWriters=@(); failure=$null
        }) -Force
    }
    $State.step = 7; $State.postflight.startedAt = [DateTime]::UtcNow.ToString('o'); $State.postflight.status='running'; $State.status='step7-postflight-running'; Write-RestoreState -State $State -WorkDir $StateDir

    $db = Get-DatabaseSnapshot -ContainerId $ContainerId
    if ($db.ImageRowCount -ne [int64]$Manifest.counts.imageRowCount) { throw "Step-7 database Image row count $($db.ImageRowCount) does not match manifest $($Manifest.counts.imageRowCount)." }
    $State.postflight.databaseVerified=$true; Write-RestoreState -State $State -WorkDir $StateDir

    Invoke-PythonScript -ScriptPath $script:StageHelper -Arguments @('--backup-dir',$BackupDir,'--staged-files-root',$FilesRoot,'--allow-benign-runtime-staging')
    $State.postflight.filesInventoryVerified=$true; Write-RestoreState -State $State -WorkDir $StateDir

    $catalogueJson = Join-Path $postflightDir 'image-catalogue.json'; $catalogueRows = @(Export-ImageCatalogueJson -ContainerId $ContainerId -OutputPath $catalogueJson)
    $reconciliationReport = Join-Path $postflightDir 'catalogue-files-reconciliation.json'
    Invoke-PythonScript -ScriptPath $script:PostflightHelper -Arguments @('--files-root',$FilesRoot,'--catalogue-json',$catalogueJson,'--expected-image-count',([string][int64]$Manifest.counts.imageRowCount),'--output',$reconciliationReport)
    $reconciliation = Get-Content -LiteralPath $reconciliationReport -Raw -Encoding UTF8 | ConvertFrom-Json
    $representativeImage = $reconciliation.representativeImage
    if ($null -eq $representativeImage) { throw 'Step-7 requires a representative IMAGE row, but the restored catalogue is empty.' }
    $marqueeId = Get-RepresentativeMarqueeId -ContainerId $ContainerId
    $State.postflight.catalogueReconciliationVerified=$true; $State.postflight.representativeMarqueeId=$marqueeId; $State.postflight.representativeImageId=[int64]$representativeImage.id; $State.postflight.representativeImagePath=[string]$representativeImage.relativePath
    Write-RestoreState -State $State -WorkDir $StateDir

    $probe = $null
    try {
        $probe = Start-PostflightProbeResponder -Mode $ModeName -PostflightDir $postflightDir
        if ([string]$probe.Kind -eq 'direct') { Invoke-DirectResponderHealthCheck -ConfigPath ([string]$probe.ConfigPath) }
        else { Wait-ForContainerHealthy -ContainerId ([string]$probe.ContainerId) -Seconds 120 }
        $State.postflight.responderHealthVerified=$true; Write-RestoreState -State $State -WorkDir $StateDir

        $logs = Get-PostflightProbeLogs -Probe $probe
        [System.IO.File]::WriteAllText((Join-Path $postflightDir 'responder-startup.log'), $logs + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
        if ($logs -notmatch 'synchronise: ok') { throw 'Responder startup did not report retained-tree reconciliation "synchronise: ok".' }
        if ($logs -notmatch 'sizeof\(databaseMap\)\s*=') { throw 'Responder startup log did not report retained databaseMap replay size.' }

        $brokerId = Ensure-MqttInfrastructureRunning -Mode $ModeName
        $imagePayload = Get-MqttRetainedPayload -BrokerContainerId $brokerId -ConfigPath ([string]$probe.ConfigPath) -Topic ("diaries/images/" + [string]$representativeImage.id)
        if ([int64]$imagePayload.id -ne [int64]$representativeImage.id -or [string]$imagePayload.relativePath -ne [string]$representativeImage.relativePath) { throw 'Representative IMAGE retained payload does not match restored catalogue identity.' }
        $marqueePayload = Get-MqttRetainedPayload -BrokerContainerId $brokerId -ConfigPath ([string]$probe.ConfigPath) -Topic ("diaries/marquees/" + [string]$marqueeId)
        if ([int64]$marqueePayload.id -ne [int64]$marqueeId) { throw 'Representative MARQUEE retained payload does not match restored database identity.' }
        $url = Assert-RepresentativeHttpImage -Image $representativeImage -Port ([int]$probe.HttpPort) -PostflightDir $postflightDir
        $State.postflight.retainedReplayVerified=$true; $State.postflight.representativeFilesUrl=$url; Write-RestoreState -State $State -WorkDir $StateDir
    }
    finally {
        Stop-PostflightProbeResponder -Probe $probe
    }

    # The active probe has passed and has been stopped. Only now restore the exact prior writer state.
    $restored = @(Restore-PriorWriterState -State $State -PostflightDir $postflightDir)
    $State.postflight.priorWriterStateRestored=$true; $State.postflight.restoredWriters=@($restored)
    $State.postflight.completedAt=[DateTime]::UtcNow.ToString('o'); $State.postflight.status='complete'
    $State.rollback.status='closed-after-step7'
    if ($null -eq $State.rollback.PSObject.Properties['closedAt']) { $State.rollback | Add-Member -NotePropertyName closedAt -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force } else { $State.rollback.closedAt=[DateTime]::UtcNow.ToString('o') }
    if ($null -eq $State.rollback.PSObject.Properties['automaticRollbackAvailable']) { $State.rollback | Add-Member -NotePropertyName automaticRollbackAvailable -NotePropertyValue $false -Force } else { $State.rollback.automaticRollbackAvailable=$false }
    if ($null -eq $State.rollback.PSObject.Properties['artifactsRetained']) { $State.rollback | Add-Member -NotePropertyName artifactsRetained -NotePropertyValue $true -Force } else { $State.rollback.artifactsRetained=$true }
    $State.status='restore-complete'; $State.failure=$null; Write-RestoreState -State $State -WorkDir $StateDir

    Write-Host ''
    Write-Host 'STEP 7 POST-RESTORE VERIFICATION COMPLETE.'
    Write-Host "  Database:             queryable; Image rows=$($db.ImageRowCount) match manifest"
    Write-Host "  Durable Files:        exact backup inventory verified"
    Write-Host "  Catalogue/Files:      no unexplained missing/untracked/conflicting file"
    Write-Host "  Retained replay:      synchronise: ok; representative MARQUEE + IMAGE retained payloads readable"
    Write-Host "  /files mapping:       representative Image bytes verified at $($State.postflight.representativeFilesUrl)"
    Write-Host "  Prior writer state:   restored ($($restored -join ', '))"
    if ($restored.Count -eq 0) { Write-Host '  Prior writer state:   no responder was running before restore; all responders remain stopped' }
    Write-Host "  Safety backup:        retained at $($State.safetyBackup.directory)"
    Write-Host "  Pre-restore Files:    retained at $($State.rollback.filesDirectory)"
    Write-Host '  Automatic rollback:  closed after successful Step-7 acceptance'
}

$ProjectPath = [System.IO.Path]::GetFullPath($ProjectDir)
$ModeEnvironmentFile = Get-ModeEnvironmentFile -Mode $ModeName
$LocalEnvironmentFile = Join-Path $ProjectPath 'config\environments\local.env'
$ComposeFile = Get-ComposeFile -Mode $ModeName
$ManifestHelper = Join-Path $ProjectPath 'scripts\windows\common\complete-dataset-manifest.py'
$StageHelper = Join-Path $ProjectPath 'scripts\windows\common\complete-dataset-restore-stage.py'
$PostflightHelper = Join-Path $ProjectPath 'scripts\windows\common\complete-dataset-postflight.py'
$preparingDir = $null
$preparedDir = $null
$stagePath = $null
$restoreState = $null
$writersStopped = $false
$step6OperationStarted = $false
$step7OperationStarted = $false

try {
    $actionCount = @(@($PreflightOnly,$PrepareOnly,$ApplyOnly,$RollbackOnly,$PostflightOnly) | Where-Object { [bool]$_ }).Count
    if ($actionCount -ne 1) { throw 'Exactly one restore action is required: preflight, prepare, apply, rollback or postflight.' }
    foreach ($requiredFile in $ModeEnvironmentFile,$LocalEnvironmentFile,$ComposeFile,$ManifestHelper,$StageHelper,$PostflightHelper) { if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "Required file not found: $requiredFile" } }
    foreach ($command in 'docker.exe','powershell.exe','robocopy.exe') { if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Required command not found on PATH: $command" } }

    $modeEnv = Read-DotEnvFile -Path $ModeEnvironmentFile; $localEnv = Read-DotEnvFile -Path $LocalEnvironmentFile
    Import-DotEnvValues -Values $modeEnv.Values; Import-DotEnvValues -Values $localEnv.Values
    if ([string]::IsNullOrWhiteSpace($env:DIARIES_DB_NAME)) { $env:DIARIES_DB_NAME = 'diaries' }
    if ([string]::IsNullOrWhiteSpace($env:DIARIES_DB_USERNAME)) { $env:DIARIES_DB_USERNAME = 'diaries' }

    Invoke-DatasetPairValidation
    $resolved = Resolve-EffectiveDataset
    $DatasetName = [string]$resolved['DIARIES_DATASET_NAME']
    $databaseIdentity = [string]$resolved['DIARIES_EFFECTIVE_DB_DATA_DIR']
    $filesRoot = [string]$resolved['DIARIES_EFFECTIVE_FILES_ROOT']
    $sharing = [string]$resolved['DIARIES_DATASET_SHARING']

    $selected = Get-ModeSelection -Mode $ModeName
    $KnownConsumers = @()
    foreach ($candidate in $SupportedModes) {
        $selection = Get-ModeSelection -Mode $candidate
        if ($selection.DatabasePath -eq $selected.DatabasePath -and $selection.FilesDir -eq $selected.FilesDir) { $KnownConsumers += $candidate }
    }

    if (-not (Test-Path -LiteralPath $filesRoot -PathType Container)) { throw "Selected target Files root is unavailable: $filesRoot" }
    [void](Get-ChildItem -LiteralPath $filesRoot -Force -ErrorAction Stop | Select-Object -First 1)
    $targetStaging = Get-StagingInspection -FilesRoot $filesRoot

    $CurrentComposeArguments = Get-ComposeArguments -Mode $ModeName
    $dbContainerId = Get-ComposeServiceContainerId -Mode $ModeName -Service 'diaries-db'
    if ([string]::IsNullOrWhiteSpace($dbContainerId) -or -not (Test-ContainerRunning -ContainerId $dbContainerId)) { throw "The selected $ModeName diaries-db service is not running. Start that mode before restore preparation." }
    $ready = Invoke-Docker -Arguments ($CurrentComposeArguments + @('exec','-T','diaries-db','pg_isready','--username',$env:DIARIES_DB_USERNAME,'--dbname','postgres')) -CaptureOutput -AllowFailure
    if ($ready.ExitCode -ne 0) { throw 'The target PostgreSQL service is not ready.' }

    $backupDir = Resolve-BackupDirectory -InputValue $BackupInput -DatasetName $DatasetName
    if ((Split-Path -Leaf $backupDir).StartsWith('.') -or (Split-Path -Leaf $backupDir).EndsWith('.partial')) { throw "Incomplete/partial backup directories are never valid restore inputs: $backupDir" }
    Invoke-PythonScript -ScriptPath $ManifestHelper -Arguments @('verify','--backup-dir',$backupDir)
    $manifest = Read-Manifest -BackupDir $backupDir
    Assert-ManifestMatchesTarget -Manifest $manifest -DatasetName $DatasetName -DatabaseIdentity $databaseIdentity -FilesSelector $env:DIARIES_FILES_DIR -FilesRoot $filesRoot
    Test-CustomDumpWithPgRestore -BackupDir $backupDir -ContainerId $dbContainerId

    $sourceBackupId = [string]$manifest.backupId
    $filesParent = Split-Path -Parent $filesRoot; $filesLeaf = Split-Path -Leaf $filesRoot
    $stagePath = Join-Path $filesParent ".$filesLeaf.restore-$sourceBackupId.staged"
    $restoreWorkRoot = Join-Path (Join-Path $ProjectPath 'data\dataset-restores') $DatasetName
    $preparingDir = Join-Path $restoreWorkRoot ".$sourceBackupId.preparing"
    $preparedDir = Join-Path $restoreWorkRoot "$sourceBackupId.prepared"

    if ($ApplyOnly -or $RollbackOnly -or $PostflightOnly) {
        if (-not (Test-Path -LiteralPath $preparedDir -PathType Container)) { throw "Prepared Step-5 restore state not found: $preparedDir" }
        $restoreState = Read-RestoreState -PreparedDir $preparedDir
        Assert-PreparedStateMatchesCurrentTarget -State $restoreState -SourceBackupId $sourceBackupId -BackupDir $backupDir -DatasetName $DatasetName -DatabaseIdentity $databaseIdentity -FilesSelector $env:DIARIES_FILES_DIR -FilesRoot $filesRoot
        Ensure-Step6StateFields -State $restoreState -SourceBackupId $sourceBackupId -FilesRoot $filesRoot
        $safetyBackupDir = [System.IO.Path]::GetFullPath([string]$restoreState.safetyBackup.directory)
        if (-not (Test-Path -LiteralPath $safetyBackupDir -PathType Container)) { throw "Mandatory safety backup directory is missing: $safetyBackupDir" }
        Invoke-PythonScript -ScriptPath $ManifestHelper -Arguments @('verify','--backup-dir',$safetyBackupDir)
        $safetyManifest = Read-Manifest -BackupDir $safetyBackupDir
        Assert-ManifestMatchesTarget -Manifest $safetyManifest -DatasetName $DatasetName -DatabaseIdentity $databaseIdentity -FilesSelector $env:DIARIES_FILES_DIR -FilesRoot $filesRoot
        Wait-ForWriterStop

        if ($ApplyOnly) {
            if ([string]$restoreState.status -ne 'prepared-awaiting-step6') { throw "Restore state is not ready for Step 6 apply; current status: $($restoreState.status)" }
            if (-not (Test-Path -LiteralPath $stagePath -PathType Container)) { throw "Prepared replacement Files stage is missing: $stagePath" }
            Invoke-PythonScript -ScriptPath $StageHelper -Arguments @('--backup-dir',$backupDir,'--staged-files-root',$stagePath)
            [void](Get-StagingInspection -FilesRoot $filesRoot)
            $beforeDb = Get-DatabaseSnapshot -ContainerId $dbContainerId
            if ($beforeDb.ImageRowCount -ne [int64]$safetyManifest.counts.imageRowCount) { throw "Current database Image row count ($($beforeDb.ImageRowCount)) no longer matches the mandatory safety backup ($($safetyManifest.counts.imageRowCount)); refusing destructive apply." }
            if (Test-Path -LiteralPath ([string]$restoreState.apply.files.rollbackDirectory)) { throw "Step-6 rollback Files path already exists: $($restoreState.apply.files.rollbackDirectory)" }

            Write-Host ''
            Write-Host 'Diaries complete-dataset restore Step-6 apply'
            Write-Host "  Restore source:       $backupDir"
            Write-Host "  Safety backup:        $safetyBackupDir"
            Write-Host "  Database before:      OID=$($beforeDb.Oid), Image rows=$($beforeDb.ImageRowCount)"
            Write-Host "  Files stage:          $stagePath"
            Write-Host "  Files rollback path:  $($restoreState.apply.files.rollbackDirectory)"
            Write-Host '  Writers:              quiesced and will remain stopped for Step 7'
            Write-Host ''
            Write-Host 'WARNING: APPLY will now replace both PostgreSQL and the live Files root.' -ForegroundColor Yellow
            Write-Host 'The original Files root and mandatory safety backup are retained for rollback.' -ForegroundColor Yellow
            $confirmation = Read-Host 'Type APPLY to continue'
            if ($confirmation -cne 'APPLY') { Write-Host 'Step-6 apply cancelled; prepared state remains unchanged.'; exit 1 }
            $step6OperationStarted = $true

            $restoreState.step = 6; $restoreState.apply.confirmation.received = $true; $restoreState.apply.confirmation.at = [DateTime]::UtcNow.ToString('o'); $restoreState.apply.startedAt = [DateTime]::UtcNow.ToString('o')
            $restoreState.apply.database.beforeOid = $beforeDb.Oid; $restoreState.apply.database.beforeImageRowCount = $beforeDb.ImageRowCount
            $restoreState.status = 'step6-apply-started'; Write-RestoreState -State $restoreState -WorkDir $preparedDir

            Invoke-DatabaseRestoreFromCompleteBackup -BackupDir $backupDir -ContainerId $dbContainerId -State $restoreState -Progress $restoreState.apply.database -StateDir $preparedDir
            $afterDb = Get-DatabaseSnapshot -ContainerId $dbContainerId
            $restoreState.apply.database.afterOid = $afterDb.Oid; $restoreState.apply.database.afterImageRowCount = $afterDb.ImageRowCount
            if ($afterDb.ImageRowCount -ne [int64]$manifest.counts.imageRowCount) { throw "Restored database Image row count ($($afterDb.ImageRowCount)) does not match selected backup manifest ($($manifest.counts.imageRowCount))." }
            $restoreState.status = 'step6-applying-files'; Write-RestoreState -State $restoreState -WorkDir $preparedDir
            Invoke-FilesApplySwap -State $restoreState -StateDir $preparedDir -BackupDir $backupDir -FilesRoot $filesRoot -StagePath $stagePath
            Wait-ForWriterStop
            $restoreState.apply.completedAt = [DateTime]::UtcNow.ToString('o'); $restoreState.status = 'applied-awaiting-step7'; Write-RestoreState -State $restoreState -WorkDir $preparedDir

            Write-Host ''
            Write-Host 'STEP 6 COMPLETE-DATASET APPLY COMPLETE.'
            Write-Host "  Database after:       OID=$($afterDb.Oid), Image rows=$($afterDb.ImageRowCount)"
            Write-Host "  Files after:          $($restoreState.apply.files.fileCount) files / $($restoreState.apply.files.totalBytes) bytes; exact inventory verified"
            Write-Host "  Runtime staging:      empty $StagingName recreated; stale staging payloads were not restored"
            Write-Host "  Rollback Files:       $($restoreState.apply.files.rollbackDirectory)"
            Write-Host "  Safety backup:        $safetyBackupDir"
            Write-Host "  Rollback command:     restore-dataset.bat rollback $sourceBackupId"
            Write-Host '  Writers:              STOPPED - Step 7 postflight must succeed before prior writer state may be restored'
            exit 0
        }

        if ($PostflightOnly) {
            if ([string]$restoreState.status -notin @('applied-awaiting-step7','step7-postflight-failed')) { throw "Postflight is allowed only after Step-6 apply or a failed Step-7 attempt; current status: $($restoreState.status)" }
            $step7OperationStarted = $true
            try {
                Invoke-Step7Postflight -State $restoreState -StateDir $preparedDir -BackupDir $backupDir -Manifest $manifest -FilesRoot $filesRoot -ContainerId $dbContainerId
                exit 0
            }
            catch {
                $failure = $_.Exception.Message
                try { Stop-AllKnownWriters } catch { }
                $restoreState.status='step7-postflight-failed'
                if ($null -eq $restoreState.PSObject.Properties['postflight']) {
                    $restoreState | Add-Member -NotePropertyName postflight -NotePropertyValue ([ordered]@{status='failed';failure=$failure}) -Force
                } else {
                    $restoreState.postflight.status='failed'; $restoreState.postflight.failure=$failure
                }
                $restoreState.failure=[ordered]@{at=[DateTime]::UtcNow.ToString('o');message=$failure;databaseChanged=[bool]$restoreState.liveDataset.databaseChanged;filesRootChanged=[bool]$restoreState.liveDataset.filesRootChanged}
                Write-RestoreState -State $restoreState -WorkDir $preparedDir
                throw $failure
            }
        }

        if ($RollbackOnly) {
            if ([string]$restoreState.status -notin @('step6-apply-failed','step7-postflight-failed','applied-awaiting-step7')) { throw "Rollback is allowed only after Step-6 apply failure or before Step-7 acceptance; current status: $($restoreState.status)" }
            Write-Host ''
            Write-Host 'Diaries complete-dataset Step-6 rollback'
            Write-Host "  Safety backup:        $safetyBackupDir"
            Write-Host "  Original Files:       $($restoreState.rollback.filesDirectory)"
            Write-Host '  Writers:              quiesced and will remain stopped after rollback'
            $confirmation = Read-Host 'Type ROLLBACK to restore the mandatory pre-restore safety state'
            if ($confirmation -cne 'ROLLBACK') { Write-Host 'Rollback cancelled; current stopped restore state remains unchanged.'; exit 1 }
            $step6OperationStarted = $true

            $restoreState.rollback.startedAt = [DateTime]::UtcNow.ToString('o'); $restoreState.rollback.status = 'running'; $restoreState.status = 'step6-rollback-database'; Write-RestoreState -State $restoreState -WorkDir $preparedDir
            if ($null -eq $restoreState.PSObject.Properties['rollbackDatabase']) {
                $restoreState | Add-Member -NotePropertyName rollbackDatabase -NotePropertyValue ([ordered]@{ dropStarted=$false; dropComplete=$false; createComplete=$false; restoreComplete=$false }) -Force
            }
            Invoke-DatabaseRestoreFromCompleteBackup -BackupDir $safetyBackupDir -ContainerId $dbContainerId -State $restoreState -Progress $restoreState.rollbackDatabase -StateDir $preparedDir
            $rollbackDb = Get-DatabaseSnapshot -ContainerId $dbContainerId
            if ($rollbackDb.ImageRowCount -ne [int64]$safetyManifest.counts.imageRowCount) { throw "Rolled-back database Image row count does not match safety backup manifest." }
            $restoreState.status = 'step6-rollback-files'; Write-RestoreState -State $restoreState -WorkDir $preparedDir
            Invoke-FilesRollbackSwap -State $restoreState -StateDir $preparedDir -SafetyBackupDir $safetyBackupDir -FilesRoot $filesRoot -SourceBackupId $sourceBackupId
            $restoreState.liveDataset.databaseChanged = $false; $restoreState.rollback.completedAt = [DateTime]::UtcNow.ToString('o'); $restoreState.rollback.status = 'complete'; $restoreState.status = 'rolled-back-awaiting-review'; Write-RestoreState -State $restoreState -WorkDir $preparedDir
            Wait-ForWriterStop
            Write-Host ''
            Write-Host 'STEP 6 ROLLBACK COMPLETE.'
            Write-Host "  Database:             restored from safety backup $($restoreState.safetyBackup.backupId)"
            Write-Host '  Durable Files:        restored to the pre-restore safety state and verified'
            if ($restoreState.rollback.failedReplacementDirectory) { Write-Host "  Failed replacement:   $($restoreState.rollback.failedReplacementDirectory) (retained for diagnosis)" }
            Write-Host '  Writers:              STOPPED - review/re-preflight before any restart'
            exit 0
        }
    }
    if (Test-Path -LiteralPath $stagePath) { throw "Restore staging sibling already exists; inspect/clean the previous attempt before retrying: $stagePath" }
    if (Test-Path -LiteralPath $preparingDir) { throw "Restore preparation workspace already exists from an incomplete attempt: $preparingDir" }
    if (Test-Path -LiteralPath $preparedDir) { throw "A prepared restore for this backup already exists: $preparedDir" }

    $currentDurableBytes = Get-DurableTargetBytes -FilesRoot $filesRoot
    $restoreFilesBytes = [int64]$manifest.files.snapshot.totalBytes
    $customBytes = [int64]$manifest.database.customDump.sizeBytes; $sqlBytes = [int64]$manifest.database.sqlDump.sizeBytes
    $estimatedSafetyBytes = $currentDurableBytes + $customBytes + $sqlBytes + 67108864L
    $backupRoot = Join-Path $ProjectPath 'data\dataset-backups'
    $localFreeBytes = Get-LocalFreeBytes -PathValue $backupRoot
    if ($null -ne $localFreeBytes -and $localFreeBytes -lt $estimatedSafetyBytes) { throw "Insufficient known local free space for the mandatory safety backup estimate: need at least $estimatedSafetyBytes bytes, have $localFreeBytes bytes." }
    $targetFreeBytes = Get-LocalFreeBytes -PathValue $filesParent
    if ($null -ne $targetFreeBytes -and $targetFreeBytes -lt $restoreFilesBytes) { throw "Insufficient known target Files free space for staging: need $restoreFilesBytes bytes, have $targetFreeBytes bytes." }

    $writerState = Get-WriterState

    Write-Host ''
    Write-Host 'Diaries complete-dataset restore Step-5 preflight'
    Write-Host "  Invoking mode:          $ModeName"
    Write-Host "  Logical dataset:        $DatasetName"
    Write-Host "  Database target:        $databaseIdentity / $($env:DIARIES_DB_NAME)"
    Write-Host "  Files target:           $($env:DIARIES_FILES_DIR) -> $filesRoot"
    Write-Host "  Dataset sharing:        $sharing"
    Write-Host "  Complete backup:        $backupDir"
    Write-Host "  Backup ID:              $sourceBackupId"
    Write-Host "  Backup Files:           $($manifest.files.snapshot.fileCount) files / $restoreFilesBytes bytes"
    Write-Host '  Backup manifest:        schema-2 complete/verified'
    Write-Host '  Custom dump:            pg_restore --list verified'
    Write-Host "  Target staging:         $($targetStaging.Disposition) ($($targetStaging.EntryCount) entries)"
    Write-Host "  Replacement stage:      $stagePath"
    Write-Host "  Current durable Files:  $currentDurableBytes bytes"
    Write-Host "  Safety-backup estimate: $estimatedSafetyBytes bytes"
    if ($null -ne $localFreeBytes) { Write-Host "  Local free space:       $localFreeBytes bytes (checked)" } else { Write-Host '  Local free space:       unavailable for this path; actual safety-backup write remains authoritative' }
    if ($null -ne $targetFreeBytes) { Write-Host "  Target free space:      $targetFreeBytes bytes (checked)" } else { Write-Host '  Target free space:      unavailable for UNC/network path; actual staging copy remains authoritative' }
    foreach ($writer in $writerState.DockerResponders) { Write-Host "  Writer:                 docker:$($writer.mode)/diaries-responder running=$($writer.wasRunning)" }
    if ($writerState.DirectResponder.applicable) { Write-Host "  Writer:                 windows:direct-diaries-responder running=$($writerState.DirectResponder.wasRunning) pids=$($writerState.DirectResponder.processIds -join ',')" }

    if ($PreflightOnly) {
        Write-Host ''
        Write-Host 'PREFLIGHT OK: backup and target identities/checksums are valid; no writers were stopped, no safety backup was created, and no Files staging directory was created.'
        exit 0
    }

    Write-Host ''
    Write-Host 'WARNING: Step 5 will stop all writers for this dataset and leave them stopped for Step 6.' -ForegroundColor Yellow
    Write-Host 'It will create a mandatory complete safety backup and a verified sibling replacement Files stage.' -ForegroundColor Yellow
    Write-Host 'It will NOT drop/restore PostgreSQL and will NOT replace the live Files root in this step.' -ForegroundColor Yellow
    $confirmation = Read-Host 'Type RESTORE to prepare this complete-dataset restore'
    if ($confirmation -cne 'RESTORE') { throw 'Restore preparation cancelled: explicit RESTORE confirmation was not supplied.' }

    $restoreState = [ordered]@{
        schemaVersion = 1; feature = '0033-FEAT'; step = 5; status = 'confirmation-received';
        restoreSource = [ordered]@{ backupId = $sourceBackupId; directory = $backupDir; manifest = 'dataset-manifest.json'; manifestValidated = $true; customDumpPgRestoreListVerified = $true }
        target = [ordered]@{ logicalDataset = $DatasetName; databaseStorageIdentity = $databaseIdentity; databaseName = $env:DIARIES_DB_NAME; filesSelector = $env:DIARIES_FILES_DIR; resolvedFilesRoot = $filesRoot; datasetSharing = $sharing }
        confirmation = [ordered]@{ requiredToken = 'RESTORE'; received = $true; at = [DateTime]::UtcNow.ToString('o') }
        priorWriters = [ordered]@{ dockerResponders = @($writerState.DockerResponders); directResponder = $writerState.DirectResponder; quiesced = $false }
        targetStaging = [ordered]@{ disposition = $targetStaging.Disposition; entryCount = $targetStaging.EntryCount; note = $targetStaging.Note; recheckedAfterQuiescence = $false }
        space = [ordered]@{ currentDurableFilesBytes = $currentDurableBytes; replacementFilesBytes = $restoreFilesBytes; estimatedSafetyBackupBytes = $estimatedSafetyBytes; knownLocalFreeBytes = $localFreeBytes; knownTargetFreeBytes = $targetFreeBytes }
        safetyBackup = [ordered]@{ required = $true; backupId = $null; directory = $null; verified = $false }
        stagedFiles = [ordered]@{ directory = $stagePath; copied = $false; inventoryVerified = $false; fileCount = [int64]$manifest.files.snapshot.fileCount; totalBytes = $restoreFilesBytes }
        liveDataset = [ordered]@{ databaseChanged = $false; filesRootChanged = $false }
        startedAt = [DateTime]::UtcNow.ToString('o'); preparedAt = $null; failure = $null
    }
    Write-RestoreState -State $restoreState -WorkDir $preparingDir

    Stop-Writers -WriterState $writerState; $writersStopped = $true
    $restoreState.priorWriters.quiesced = $true; $restoreState.status = 'writers-quiesced'
    $targetStaging = Get-StagingInspection -FilesRoot $filesRoot
    $restoreState.targetStaging.disposition = $targetStaging.Disposition; $restoreState.targetStaging.entryCount = $targetStaging.EntryCount; $restoreState.targetStaging.note = $targetStaging.Note; $restoreState.targetStaging.recheckedAfterQuiescence = $true
    Write-RestoreState -State $restoreState -WorkDir $preparingDir

    $safetyBackupId = New-SafetyBackupId -DatasetName $DatasetName
    $safetyBackupPath = Join-Path (Join-Path (Join-Path $ProjectPath 'data\dataset-backups') $DatasetName) $safetyBackupId
    $restoreState.safetyBackup.backupId = $safetyBackupId; $restoreState.status = 'creating-safety-backup'; Write-RestoreState -State $restoreState -WorkDir $preparingDir
    Invoke-SafetyBackup -SafetyBackupId $safetyBackupId
    $restoreState.safetyBackup.directory = $safetyBackupPath; $restoreState.safetyBackup.verified = $true; $restoreState.status = 'safety-backup-complete'; Write-RestoreState -State $restoreState -WorkDir $preparingDir

    Write-Host ''
    Write-Host "Staging replacement Files to sibling path: $stagePath"
    Copy-BackupFilesToStage -BackupDir $backupDir -StagePath $stagePath
    $restoreState.stagedFiles.copied = $true; $restoreState.status = 'verifying-staged-files'; Write-RestoreState -State $restoreState -WorkDir $preparingDir
    Invoke-PythonScript -ScriptPath $StageHelper -Arguments @('--backup-dir',$backupDir,'--staged-files-root',$stagePath)
    $restoreState.stagedFiles.inventoryVerified = $true

    # Final Step-5 proof: writers still stopped, transient target staging still benign,
    # and the selected backup remains independently valid before handing off to Step 6.
    Wait-ForWriterStop
    [void](Get-StagingInspection -FilesRoot $filesRoot)
    Invoke-PythonScript -ScriptPath $ManifestHelper -Arguments @('verify','--backup-dir',$backupDir)

    $restoreState.status = 'prepared-awaiting-step6'; $restoreState.preparedAt = [DateTime]::UtcNow.ToString('o')
    Write-RestoreState -State $restoreState -WorkDir $preparingDir
    Move-Item -LiteralPath $preparingDir -Destination $preparedDir
    $preparingDir = $null

    Write-Host ''
    Write-Host 'STEP 5 RESTORE PREPARATION COMPLETE.'
    Write-Host "  Restore source:       $backupDir"
    Write-Host "  Safety backup:        $safetyBackupPath"
    Write-Host "  Staged replacement:   $stagePath"
    Write-Host "  Prepared state:       $preparedDir\restore-state.json"
    Write-Host '  Writers:              quiesced and intentionally left stopped'
    Write-Host '  Live database:         UNCHANGED'
    Write-Host '  Live Files root:       UNCHANGED'
    Write-Host '  Next action:           Step 6 applies database + Files as one controlled operation.'
    exit 0
}
catch {
    $message = $_.Exception.Message
    if ($PostflightOnly -and $step7OperationStarted) {
        try { Stop-AllKnownWriters } catch { }
        Write-Error $message
        Write-Host 'STEP 7 POSTFLIGHT FAILED. All known responders are stopped; automatic prior-state restart was not accepted.' -ForegroundColor Yellow
        if ($null -ne $restoreState) {
            Write-Host "Mandatory safety backup: $($restoreState.safetyBackup.directory)" -ForegroundColor Yellow
            Write-Host "Pre-restore Files rollback: $($restoreState.rollback.filesDirectory)" -ForegroundColor Yellow
            Write-Host "Rollback command: restore-dataset.bat rollback $sourceBackupId" -ForegroundColor Yellow
        }
        exit 1
    }
    if ($step6OperationStarted -and $null -ne $restoreState -and $preparedDir -and (Test-Path -LiteralPath $preparedDir -PathType Container) -and ($ApplyOnly -or $RollbackOnly)) {
        try {
            if ($RollbackOnly) {
                $restoreState.status = 'step6-rollback-failed'
                if ($null -ne $restoreState.PSObject.Properties['rollback']) { $restoreState.rollback.status = 'failed' }
            } else {
                $restoreState.status = 'step6-apply-failed'
            }
            $restoreState.failure = [ordered]@{ at = [DateTime]::UtcNow.ToString('o'); message = $message; databaseChanged = [bool]$restoreState.liveDataset.databaseChanged; filesRootChanged = [bool]$restoreState.liveDataset.filesRootChanged }
            Write-RestoreState -State $restoreState -WorkDir $preparedDir
        } catch { }
    }
    elseif ($null -ne $restoreState -and $preparingDir) {
        try {
            $restoreState.status = 'prepare-failed'; $restoreState.failure = [ordered]@{ at = [DateTime]::UtcNow.ToString('o'); message = $message }
            Write-RestoreState -State $restoreState -WorkDir $preparingDir
        } catch { }
    }
    Write-Error $message
    if (($ApplyOnly -or $RollbackOnly) -and $step6OperationStarted) {
        Write-Host 'Writers remain intentionally stopped after Step-6 failure.' -ForegroundColor Yellow
        if ($null -ne $restoreState) {
            Write-Host "Database changed: $($restoreState.liveDataset.databaseChanged); Files root changed: $($restoreState.liveDataset.filesRootChanged)" -ForegroundColor Yellow
            Write-Host "Mandatory safety backup: $($restoreState.safetyBackup.directory)" -ForegroundColor Yellow
            Write-Host "Rollback command: restore-dataset.bat rollback $sourceBackupId" -ForegroundColor Yellow
            if ($null -ne $restoreState.PSObject.Properties['apply']) { Write-Host "Original Files rollback path: $($restoreState.apply.files.rollbackDirectory)" -ForegroundColor Yellow }
        }
    }
    elseif ($ApplyOnly -or $RollbackOnly) {
        Write-Host 'No destructive Step-6 operation started; the existing prepared/stopped state was not rewritten.' -ForegroundColor Yellow
    }
    elseif ($writersStopped) { Write-Host 'Writers remain intentionally stopped after restore-preparation failure. Inspect restore-state.json before recovery/retry.' -ForegroundColor Yellow }
    if ($preparingDir -and (Test-Path -LiteralPath $preparingDir -PathType Container)) { Write-Host "Incomplete restore-preparation workspace retained: $preparingDir" -ForegroundColor Yellow }
    if ($stagePath -and (Test-Path -LiteralPath $stagePath -PathType Container)) { Write-Host "Staged Files directory retained for diagnosis: $stagePath" -ForegroundColor Yellow }
    exit 1
}
