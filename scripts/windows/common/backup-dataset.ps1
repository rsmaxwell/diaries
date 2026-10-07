param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('development-infrastructure', 'local-docker-build', 'local-published-smoke')]
    [string]$ModeName,

    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [switch]$PreflightOnly,

    [ValidatePattern('^\d{8}-\d{6}Z$')]
    [string]$BackupId,

    [ValidatePattern('^\d{8}-\d{6}Z$')]
    [string]$FinaliseBackupId
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

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Environment file does not exist: $Path"
    }

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
    foreach ($key in $Values.Keys) {
        [Environment]::SetEnvironmentVariable([string]$key, [string]$Values[$key], 'Process')
    }
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
    if ($dbOverride -xor $filesOverride) {
        throw "Dataset override mismatch in $($script:LocalEnvironmentFile): $DatabaseKey and $FilesKey must be overridden together."
    }

    $database = if ($dbOverride) { [string]$localEnv.Values[$DatabaseKey] } else { [string]$modeEnv.Values[$DatabaseKey] }
    $files = if ($filesOverride) { [string]$localEnv.Values[$FilesKey] } else { [string]$modeEnv.Values[$FilesKey] }

    $databasePath = if ([System.IO.Path]::IsPathRooted($database)) {
        [System.IO.Path]::GetFullPath($database)
    } else {
        [System.IO.Path]::GetFullPath((Join-Path $script:ProjectPath $database))
    }

    [pscustomobject]@{
        Mode = $Mode
        DatabaseDataDir = $database
        DatabasePath = $databasePath
        DatasetName = Split-Path -Leaf $databasePath
        FilesDir = $files
        ModeEnvironmentFile = $modeFile
    }
}

function Invoke-DatasetPairValidation {
    $validator = Join-Path $script:ProjectPath 'scripts\windows\common\validate-dataset-pair.ps1'
    if (-not (Test-Path -LiteralPath $validator -PathType Leaf)) {
        throw "Dataset-pair validator not found: $validator"
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $validator `
        -ModeName $ModeName `
        -ModeEnvironmentFile $script:ModeEnvironmentFile `
        -LocalEnvironmentFile $script:LocalEnvironmentFile
    if ($LASTEXITCODE -ne 0) {
        throw "Existing dataset-pair validation failed for $ModeName."
    }
}

function Get-StagingInspection {
    param([Parameter(Mandatory = $true)][string]$FilesRoot)

    $stagingPath = Join-Path $FilesRoot $StagingName
    $entries = @()
    $disposition = 'empty'
    $note = 'source .image-staging absent or empty; transient staging excluded from snapshot'

    if (Test-Path -LiteralPath $stagingPath) {
        if (-not (Test-Path -LiteralPath $stagingPath -PathType Container)) {
            throw "$StagingName exists but is not a directory: $stagingPath"
        }

        $stagingDirectory = Get-Item -LiteralPath $stagingPath -Force -ErrorAction Stop
        $entries = @(Get-ChildItem -LiteralPath $stagingPath -Force -Recurse -ErrorAction Stop)
        if ($entries.Count -eq 1) {
            $entry = $entries[0]
            $isExpectedCatalogueLock = (-not $entry.PSIsContainer) -and
                ($entry.Name -eq 'catalogue.lock') -and
                ($entry.Directory.FullName -eq $stagingDirectory.FullName) -and
                ([int64]$entry.Length -eq 0)
            if ($isExpectedCatalogueLock) {
                $disposition = 'excluded-benign'
                $note = 'source .image-staging contains only the expected zero-byte catalogue.lock; transient staging excluded from snapshot'
            }
        }

        $benignExpectedState = ($entries.Count -eq 0) -or ($disposition -eq 'excluded-benign')
        if (-not $benignExpectedState) {
            $sample = @($entries | Select-Object -First 5 | ForEach-Object { $_.FullName }) -join '; '
            throw "Refusing complete-dataset capture: $StagingName contains $($entries.Count) unexplained entr$(if ($entries.Count -eq 1) {'y'} else {'ies'}). Only an empty directory or the expected zero-byte catalogue.lock is permitted. Sample: $sample"
        }
    }

    [pscustomobject]@{
        Path = $stagingPath
        Entries = @($entries)
        EntryCount = $entries.Count
        Disposition = $disposition
        Note = $note
    }
}

function Resolve-EffectiveDataset {
    $resolver = Join-Path $script:ProjectPath 'scripts\windows\common\resolve-effective-dataset.ps1'
    $records = & $resolver `
        -ModeName $ModeName `
        -ProjectDir $script:ProjectPath `
        -DatabaseDataDir $env:DIARIES_DB_DATA_DIR `
        -FilesDir $env:DIARIES_FILES_DIR

    $resolved = @{}
    foreach ($record in $records) {
        $line = [string]$record
        $equals = $line.IndexOf('=')
        if ($equals -gt 0) {
            $resolved[$line.Substring(0, $equals)] = $line.Substring($equals + 1)
        }
    }

    foreach ($required in 'DIARIES_DATASET_NAME','DIARIES_EFFECTIVE_DB_DATA_DIR','DIARIES_EFFECTIVE_FILES_ROOT','DIARIES_DATASET_SHARING') {
        if (-not $resolved.ContainsKey($required) -or [string]::IsNullOrWhiteSpace([string]$resolved[$required])) {
            throw "Effective dataset resolver did not return $required."
        }
    }
    $resolved
}

function Get-ComposeFile {
    param([Parameter(Mandatory = $true)][string]$Mode)
    Join-Path $script:ProjectPath "compose.$Mode.yaml"
}

function Get-ComposeArguments {
    param([Parameter(Mandatory = $true)][string]$Mode)
    $modeFile = Get-ModeEnvironmentFile -Mode $Mode
    $composeFile = Get-ComposeFile -Mode $Mode
    @('compose', '--env-file', $modeFile, '--env-file', $script:LocalEnvironmentFile, '-f', $composeFile)
}

function Invoke-Docker {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$CaptureOutput,
        [switch]$AllowFailure
    )

    if ($CaptureOutput) {
        $output = & docker.exe @Arguments 2>&1
        $code = $LASTEXITCODE
        if (-not $AllowFailure -and $code -ne 0) {
            throw "docker command failed with exit code ${code}: docker $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)"
        }
        return [pscustomobject]@{ ExitCode = $code; Output = @($output) }
    }

    & docker.exe @Arguments
    $code = $LASTEXITCODE
    if (-not $AllowFailure -and $code -ne 0) {
        throw "docker command failed with exit code ${code}: docker $($Arguments -join ' ')"
    }
    return $code
}

function Get-ComposeServiceContainerId {
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$Service
    )
    $args = (Get-ComposeArguments -Mode $Mode) + @('ps', '-q', $Service)
    $result = Invoke-Docker -Arguments $args -CaptureOutput -AllowFailure
    if ($result.ExitCode -ne 0) { return $null }
    foreach ($line in $result.Output) {
        $value = ([string]$line).Trim()
        if ($value) { return $value }
    }
    return $null
}

function Test-ContainerRunning {
    param([Parameter(Mandatory = $true)][string]$ContainerId)
    $result = Invoke-Docker -Arguments @('inspect', '--format', '{{.State.Running}}', $ContainerId) -CaptureOutput -AllowFailure
    if ($result.ExitCode -ne 0) { return $false }
    return (([string]($result.Output | Select-Object -First 1)).Trim().ToLowerInvariant() -eq 'true')
}

function Get-DirectWriterProcesses {
    try {
        $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'java.exe'" -ErrorAction Stop)
    }
    catch {
        throw "Unable to inspect local Java writer processes through Win32_Process: $($_.Exception.Message)"
    }

    $knownResponder = @()
    $unknownPotential = @()
    foreach ($process in $processes) {
        $command = [string]$process.CommandLine
        if ([string]::IsNullOrWhiteSpace($command)) { continue }
        if ($command.Contains($DirectResponderMain)) {
            $knownResponder += $process
            continue
        }
        foreach ($main in $PotentialDirectWriterMains) {
            if ($command.Contains($main)) {
                $unknownPotential += $process
                break
            }
        }
    }
    [pscustomobject]@{ Responders = @($knownResponder); PotentialWriters = @($unknownPotential) }
}

function Stop-DockerResponder {
    param([Parameter(Mandatory = $true)][string]$Mode)
    $args = (Get-ComposeArguments -Mode $Mode) + @('stop', 'diaries-responder')
    [void](Invoke-Docker -Arguments $args)
}

function Test-DockerResponderRunning {
    param([Parameter(Mandatory = $true)][string]$Mode)
    $id = Get-ComposeServiceContainerId -Mode $Mode -Service 'diaries-responder'
    return (-not [string]::IsNullOrWhiteSpace($id)) -and (Test-ContainerRunning -ContainerId $id)
}

function Wait-ForWriterStop {
    param([int]$Seconds = 20)
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $running = @()
        foreach ($mode in $script:KnownConsumers) {
            if ($mode -ne 'development-infrastructure' -and (Test-DockerResponderRunning -Mode $mode)) {
                $running += "docker:$mode/diaries-responder"
            }
        }
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

function Invoke-DatabaseScalar {
    param([Parameter(Mandatory = $true)][string]$Sql)
    $args = $script:CurrentComposeArguments + @(
        'exec','-T','diaries-db','psql','-X','-A','-t',
        '--username', $env:DIARIES_DB_USERNAME,
        '--dbname', $env:DIARIES_DB_NAME,
        '-c', $Sql
    )
    $result = Invoke-Docker -Arguments $args -CaptureOutput
    $value = ([string]($result.Output | Select-Object -First 1)).Trim()
    if ($value -notmatch '^\d+$') { throw "Database scalar query returned an unexpected value '$value' for: $Sql" }
    return [int64]$value
}

function Invoke-PostgresDumpToContainer {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('custom','plain')][string]$Format,
        [Parameter(Mandatory = $true)][string]$ContainerPath
    )
    $args = $script:CurrentComposeArguments + @(
        'exec','-T','diaries-db','pg_dump',
        "--format=$Format", '--no-owner', '--no-privileges',
        '--username', $env:DIARIES_DB_USERNAME,
        '--dbname', $env:DIARIES_DB_NAME,
        "--file=$ContainerPath"
    )
    [void](Invoke-Docker -Arguments $args)
}

function Copy-ContainerFileToHost {
    param(
        [Parameter(Mandatory = $true)][string]$ContainerId,
        [Parameter(Mandatory = $true)][string]$ContainerPath,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    [void](Invoke-Docker -Arguments @('cp', "${ContainerId}:${ContainerPath}", $Destination))
    if (-not (Test-Path -LiteralPath $Destination -PathType Leaf)) { throw "docker cp did not create $Destination" }
    if ((Get-Item -LiteralPath $Destination).Length -le 0) { throw "Captured database file is empty: $Destination" }
}

function Remove-ContainerTemporaryFile {
    param([string]$ContainerId, [string]$ContainerPath)
    if ([string]::IsNullOrWhiteSpace($ContainerId) -or [string]::IsNullOrWhiteSpace($ContainerPath)) { return }
    [void](Invoke-Docker -Arguments @('exec', $ContainerId, 'rm', '-f', $ContainerPath) -AllowFailure)
}

function Copy-DurableFiles {
    param([Parameter(Mandatory = $true)][string]$Source, [Parameter(Mandatory = $true)][string]$Destination)
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $stagingPath = Join-Path $Source $StagingName
    $args = @(
        $Source, $Destination,
        '/E', '/COPY:DAT', '/DCOPY:DAT', '/R:2', '/W:1', '/XJ',
        '/XD', $stagingPath,
        '/NFL', '/NDL', '/NP'
    )
    & robocopy.exe @args
    $code = $LASTEXITCODE
    if ($code -ge 8) { throw "robocopy failed with exit code $code while capturing durable Files." }
}

function Write-CaptureState {
    param(
        [Parameter(Mandatory = $true)][object]$State,
        [Parameter(Mandatory = $true)][string]$Workspace
    )
    $path = Join-Path $Workspace 'capture-state.json'
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, (($State | ConvertTo-Json -Depth 12) + [Environment]::NewLine), $utf8NoBom)
}

function Read-CaptureState {
    param([Parameter(Mandatory = $true)][string]$Workspace)
    $path = Join-Path $Workspace 'capture-state.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Step-3 capture state is missing: $path"
    }
    try {
        return (Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json)
    }
    catch {
        throw "Step-3 capture state is not readable JSON: $path ($($_.Exception.Message))"
    }
}

function Set-StateProperty {
    param(
        [Parameter(Mandatory = $true)][object]$Target,
        [Parameter(Mandatory = $true)][string]$Name,
        [AllowNull()][object]$Value
    )
    if ($Target -is [System.Collections.IDictionary]) {
        $Target[$Name] = $Value
        return
    }
    $property = $Target.PSObject.Properties[$Name]
    if ($null -ne $property) {
        $property.Value = $Value
    } else {
        $Target | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) { throw "Python helper not found: $ScriptPath" }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    $prefix = @()
    if ($null -eq $python) {
        $python = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($null -ne $python) { $prefix = @('-3') }
    }
    if ($null -eq $python) { throw 'Python 3 is required for complete-dataset verification/manifest generation.' }

    $output = & $python.Source @prefix $ScriptPath @Arguments 2>&1
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "Python helper failed with exit code ${code}: $ScriptPath $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)"
    }
    foreach ($line in $output) { Write-Host ([string]$line) }
}

function Test-CustomDumpWithPgRestore {
    param(
        [Parameter(Mandatory = $true)][string]$Workspace,
        [Parameter(Mandatory = $true)][string]$ContainerId
    )
    $dump = Join-Path $Workspace 'database\diaries.dump'
    if (-not (Test-Path -LiteralPath $dump -PathType Leaf)) { throw "Custom dump is missing: $dump" }
    $containerPath = "/tmp/diaries-0033-verify-$([Guid]::NewGuid().ToString('N')).dump"
    try {
        [void](Invoke-Docker -Arguments @('cp', $dump, "${ContainerId}:${containerPath}"))
        $result = Invoke-Docker -Arguments @('exec', $ContainerId, 'pg_restore', '--list', $containerPath) -CaptureOutput
        if ($result.Output.Count -eq 0) { throw 'pg_restore --list returned no archive catalogue output.' }
    }
    finally {
        try { [void](Invoke-Docker -Arguments @('exec', $ContainerId, 'rm', '-f', $containerPath) -AllowFailure) } catch { }
    }
}

function Get-WriterDescriptionsFromState {
    param([Parameter(Mandatory = $true)][object]$State)
    $descriptions = @()
    foreach ($writer in @($State.writers.dockerResponders)) {
        $descriptions += "docker:$($writer.mode)/$($writer.service) wasRunning=$([bool]$writer.wasRunning) stoppedByCapture=$([bool]$writer.stoppedByCapture)"
    }
    if ($State.writers.directResponder.applicable) {
        $descriptions += "windows:direct-diaries-responder wasRunning=$([bool]$State.writers.directResponder.wasRunning) stoppedByCapture=$([bool]$State.writers.directResponder.stoppedByCapture)"
    }
    if ($descriptions.Count -eq 0) { $descriptions += 'no application writer applicable to captured dataset' }
    return $descriptions
}

function Assert-CaptureStateMatchesCurrentDataset {
    param(
        [Parameter(Mandatory = $true)][object]$State,
        [Parameter(Mandatory = $true)][string]$ExpectedBackupId,
        [Parameter(Mandatory = $true)][string]$DatasetName,
        [Parameter(Mandatory = $true)][string]$DatabaseIdentity,
        [Parameter(Mandatory = $true)][string]$FilesSelector,
        [Parameter(Mandatory = $true)][string]$FilesRoot
    )
    if ([int]$State.schemaVersion -ne 1 -or [string]$State.feature -ne '0033-FEAT') { throw 'Unsupported/mismatched capture-state.json.' }
    if ([string]$State.backupId -ne $ExpectedBackupId) { throw "capture-state backupId does not match candidate directory: $($State.backupId)" }
    if ([string]$State.logicalDataset -ne $DatasetName) { throw "capture-state logical dataset '$($State.logicalDataset)' does not match current effective dataset '$DatasetName'." }
    if ([string]$State.effectiveDatabaseDataDir -ne $DatabaseIdentity) { throw 'capture-state database identity does not match the current effective database identity.' }
    if ([string]$State.effectiveFilesDir -ne $FilesSelector) { throw 'capture-state Files selector does not match the current effective Files selector.' }
    if ([string]$State.resolvedPhysicalFilesRoot -ne $FilesRoot) { throw 'capture-state resolved Files root does not match the current effective Files root.' }
    if (-not [bool]$State.writers.quiesced) { throw 'capture-state does not prove application writers were quiesced during capture.' }
    $allowed = @('captured-awaiting-step4-finalisation', 'finalisation-failed-incomplete', 'step4-verified-awaiting-promotion')
    if ($allowed -notcontains [string]$State.status) { throw "Candidate capture-state status is not finalisable: $($State.status)" }
}

function Start-DockerResponder {
    param([Parameter(Mandatory = $true)][string]$Mode)
    $args = (Get-ComposeArguments -Mode $Mode) + @('start', 'diaries-responder')
    [void](Invoke-Docker -Arguments $args)
    $deadline = (Get-Date).AddSeconds(30)
    do {
        if (Test-DockerResponderRunning -Mode $Mode) { return }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Prior Docker responder state could not be restored for $Mode."
}

function Start-DirectResponder {
    param([Parameter(Mandatory = $true)][string]$RestartCommand)
    $restartPath = if ([System.IO.Path]::IsPathRooted($RestartCommand)) {
        $RestartCommand
    } else {
        Join-Path $script:ProjectPath $RestartCommand
    }
    if (-not (Test-Path -LiteralPath $restartPath -PathType Leaf)) { throw "Direct responder restart command not found: $restartPath" }
    Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', 'start', '""', "`"$restartPath`"") -WorkingDirectory $script:ProjectPath | Out-Null
    $deadline = (Get-Date).AddSeconds(60)
    do {
        $direct = Get-DirectWriterProcesses
        if ($direct.Responders.Count -gt 0) { return }
        Start-Sleep -Milliseconds 750
    } while ((Get-Date) -lt $deadline)
    throw 'Prior direct-development responder state could not be restored.'
}

function Restore-PriorWriterState {
    param([Parameter(Mandatory = $true)][object]$State)
    foreach ($writer in @($State.writers.dockerResponders)) {
        if ([bool]$writer.wasRunning) { Start-DockerResponder -Mode ([string]$writer.mode) }
    }
    if ($State.writers.directResponder.applicable -and [bool]$State.writers.directResponder.wasRunning) {
        Start-DirectResponder -RestartCommand ([string]$State.writers.directResponder.restartCommand)
    }
}

function Invoke-CompleteBackupFinalisation {
    param(
        [Parameter(Mandatory = $true)][string]$Workspace,
        [Parameter(Mandatory = $true)][string]$FinalBackup,
        [Parameter(Mandatory = $true)][object]$State,
        [Parameter(Mandatory = $true)][string]$DbContainerId,
        [Parameter(Mandatory = $true)][string]$FilesRoot
    )

    if (-not (Test-Path -LiteralPath $Workspace -PathType Container)) { throw "Incomplete backup workspace not found: $Workspace" }
    if (Test-Path -LiteralPath $FinalBackup) { throw "Final backup directory already exists: $FinalBackup" }

    # Step 4 may be retried after a failed verification. Only derived Step-4 artifacts are rebuilt.
    $verificationDir = Join-Path $Workspace 'verification'
    $manifestPath = Join-Path $Workspace 'dataset-manifest.json'
    if (Test-Path -LiteralPath $verificationDir) { Remove-Item -LiteralPath $verificationDir -Recurse -Force }
    if (Test-Path -LiteralPath $manifestPath) { Remove-Item -LiteralPath $manifestPath -Force }

    Wait-ForWriterStop
    $stagingInspection = Get-StagingInspection -FilesRoot $FilesRoot
    Set-StateProperty -Target $State.staging -Name 'disposition' -Value $stagingInspection.Disposition
    Set-StateProperty -Target $State.staging -Name 'entryCount' -Value $stagingInspection.EntryCount
    Set-StateProperty -Target $State.staging -Name 'note' -Value $stagingInspection.Note

    Write-Host ''
    Write-Host 'Step 4 complete-backup verification'
    Write-Host "  Candidate:          $Workspace"
    Write-Host '  Writer state:       quiesced'
    Write-Host "  Source Files root:  $FilesRoot"

    Test-CustomDumpWithPgRestore -Workspace $Workspace -ContainerId $DbContainerId
    Write-Host '  Custom dump:        pg_restore --list verified'

    $verificationHelper = Join-Path $script:ProjectPath 'scripts\windows\common\complete-dataset-verification.py'
    Invoke-PythonScript -ScriptPath $verificationHelper -Arguments @('--backup-dir', $Workspace, '--source-files-root', $FilesRoot)

    $inventoryPath = Join-Path $Workspace 'verification\inventory.json'
    $inventory = Get-Content -LiteralPath $inventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $durableFileCount = [int64]$inventory.fileCount
    $totalFilesBytes = [int64]$inventory.totalBytes

    $manifestHelper = Join-Path $script:ProjectPath 'scripts\windows\common\complete-dataset-manifest.py'
    $applicationIdentity = ($State.source | ConvertTo-Json -Compress -Depth 8)
    # Windows PowerShell 5.1 can strip embedded JSON quotes while serialising native argv.
    # Pass the JSON as Base64 so Python receives the exact bytes without command-line quote ambiguity.
    $applicationIdentityBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($applicationIdentity))
    $manifestArgs = @(
        'write', '--backup-dir', $Workspace,
        '--logical-dataset', [string]$State.logicalDataset,
        '--launch-mode', [string]$State.invokingMode,
        '--database-storage-identity', [string]$State.effectiveDatabaseDataDir,
        '--database-name', [string]$State.databaseName,
        '--files-selector', [string]$State.effectiveFilesDir,
        '--files-root', [string]$State.resolvedPhysicalFilesRoot,
        '--application-identity-base64', $applicationIdentityBase64,
        '--writer-method', 'Step-3 application-writer quiescence retained through Step-4 verification',
        '--writer-evidence', 'capture-state.json plus Step-4 writer-stop recheck before verification/promotion',
        '--image-row-count', [string]$State.database.imageRowCount,
        '--catalogued-file-count', [string]$State.database.cataloguedFileCount,
        '--staging-disposition', [string]$State.staging.disposition,
        '--staging-entry-count', [string]$State.staging.entryCount,
        '--staging-note', [string]$State.staging.note,
        '--started-at', [string]$State.startedAt,
        '--completed-at', [DateTime]::UtcNow.ToString('o')
    )
    foreach ($consumer in @($State.knownConsumers)) { $manifestArgs += @('--known-consumer', [string]$consumer) }
    foreach ($writerDescription in @(Get-WriterDescriptionsFromState -State $State)) { $manifestArgs += @('--writer', [string]$writerDescription) }
    Invoke-PythonScript -ScriptPath $manifestHelper -Arguments $manifestArgs
    Invoke-PythonScript -ScriptPath $manifestHelper -Arguments @('verify', '--backup-dir', $Workspace, '--allow-partial-workspace')

    # Promotion is permitted only while writers are still demonstrably absent.
    Wait-ForWriterStop
    Set-StateProperty -Target $State -Name 'step' -Value 4
    Set-StateProperty -Target $State -Name 'status' -Value 'step4-verified-awaiting-promotion'
    Set-StateProperty -Target $State -Name 'failure' -Value $null
    Write-CaptureState -State $State -Workspace $Workspace

    [System.IO.Directory]::Move($Workspace, $FinalBackup)
    try {
        Invoke-PythonScript -ScriptPath $manifestHelper -Arguments @('verify', '--backup-dir', $FinalBackup)
    }
    catch {
        # A failed normal validation must never leave a final-looking directory behind.
        if ((Test-Path -LiteralPath $FinalBackup -PathType Container) -and -not (Test-Path -LiteralPath $Workspace)) {
            [System.IO.Directory]::Move($FinalBackup, $Workspace)
        }
        throw
    }

    Set-StateProperty -Target $State -Name 'status' -Value 'complete-promoted'
    Set-StateProperty -Target $State.finalisation -Name 'promotedAt' -Value ([DateTime]::UtcNow.ToString('o'))
    Set-StateProperty -Target $State.finalisation -Name 'finalDirectory' -Value $FinalBackup
    Write-CaptureState -State $State -Workspace $FinalBackup

    try {
        Restore-PriorWriterState -State $State
        Set-StateProperty -Target $State -Name 'status' -Value 'complete-finalised'
        Set-StateProperty -Target $State.finalisation -Name 'priorWriterStateRestoredAt' -Value ([DateTime]::UtcNow.ToString('o'))
        Write-CaptureState -State $State -Workspace $FinalBackup
    }
    catch {
        Set-StateProperty -Target $State -Name 'status' -Value 'complete-writer-restore-failed'
        Set-StateProperty -Target $State -Name 'failure' -Value ([ordered]@{ at = [DateTime]::UtcNow.ToString('o'); message = $_.Exception.Message })
        try { Write-CaptureState -State $State -Workspace $FinalBackup } catch { }
        throw "Complete backup was verified and promoted, but prior writer state could not be restored: $($_.Exception.Message). Backup remains valid at $FinalBackup"
    }

    Write-Host ''
    Write-Host 'COMPLETE DATASET BACKUP COMPLETE.'
    Write-Host '  Operation:           COMPLETE DATASET backup'
    Write-Host "  Logical dataset:     $($State.logicalDataset)"
    Write-Host "  Database identity:   $($State.effectiveDatabaseDataDir) / $($State.databaseName)"
    Write-Host "  Files identity:      $($State.effectiveFilesDir) -> $($State.resolvedPhysicalFilesRoot)"
    Write-Host "  Final backup:        $FinalBackup"
    Write-Host '  Binary dump:         database\diaries.dump'
    Write-Host '  SQL dump:            database\diaries.sql'
    Write-Host "  Durable Files:       $durableFileCount files / $totalFilesBytes bytes"
    Write-Host "  Image rows:          $($State.database.imageRowCount)"
    Write-Host "  Catalogued files:    $($State.database.cataloguedFileCount)"
    Write-Host '  Manifest:            dataset-manifest.json'
    Write-Host '  Verification:        hashes/inventory/source comparison/pg_restore/manifest all verified'
    Write-Host '  Partial workspace:   none (atomically promoted)'
    Write-Host '  Prior writer state:  restored'
}

function Get-GitCommit {
    try {
        $commit = (& git.exe -C $script:ProjectPath rev-parse HEAD 2>$null | Select-Object -First 1)
        if (-not [string]::IsNullOrWhiteSpace([string]$commit)) { return ([string]$commit).Trim() }
    } catch { }
    return 'unknown'
}

$ProjectPath = [System.IO.Path]::GetFullPath($ProjectDir)
$ModeEnvironmentFile = Get-ModeEnvironmentFile -Mode $ModeName
$LocalEnvironmentFile = Join-Path $ProjectPath 'config\environments\local.env'
$ComposeFile = Get-ComposeFile -Mode $ModeName
$workspace = $null
$captureState = $null
$dbContainerId = $null
$containerDump = $null
$containerSql = $null

try {
    if ($PreflightOnly -and -not [string]::IsNullOrWhiteSpace($FinaliseBackupId)) { throw 'preflight and finalise are mutually exclusive.' }
    if (-not [string]::IsNullOrWhiteSpace($FinaliseBackupId) -and -not [string]::IsNullOrWhiteSpace($BackupId)) { throw 'BackupId and FinaliseBackupId are mutually exclusive.' }

    foreach ($requiredFile in $ModeEnvironmentFile, $LocalEnvironmentFile, $ComposeFile) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "Required file not found: $requiredFile" }
    }
    foreach ($command in 'docker.exe','powershell.exe','robocopy.exe') {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Required command not found on PATH: $command" }
    }

    # Preserve the existing precedence contract: committed mode environment first, local.env second.
    $modeEnv = Read-DotEnvFile -Path $ModeEnvironmentFile
    $localEnv = Read-DotEnvFile -Path $LocalEnvironmentFile
    Import-DotEnvValues -Values $modeEnv.Values
    Import-DotEnvValues -Values $localEnv.Values
    if ([string]::IsNullOrWhiteSpace($env:DIARIES_DB_NAME)) { $env:DIARIES_DB_NAME = 'diaries' }
    if ([string]::IsNullOrWhiteSpace($env:DIARIES_DB_USERNAME)) { $env:DIARIES_DB_USERNAME = 'diaries' }

    Invoke-DatasetPairValidation
    $resolved = Resolve-EffectiveDataset
    $datasetName = [string]$resolved['DIARIES_DATASET_NAME']
    $databaseIdentity = [string]$resolved['DIARIES_EFFECTIVE_DB_DATA_DIR']
    $filesRoot = [string]$resolved['DIARIES_EFFECTIVE_FILES_ROOT']
    $sharing = [string]$resolved['DIARIES_DATASET_SHARING']

    $selected = Get-ModeSelection -Mode $ModeName
    $KnownConsumers = @()
    foreach ($candidate in $SupportedModes) {
        $selection = Get-ModeSelection -Mode $candidate
        if ($selection.DatabasePath -eq $selected.DatabasePath -and $selection.FilesDir -eq $selected.FilesDir) {
            $KnownConsumers += $candidate
        }
    }

    $backupRoot = Join-Path $ProjectPath 'data\dataset-backups'
    $datasetBackupRoot = Join-Path $backupRoot $datasetName
    if (-not [string]::IsNullOrWhiteSpace($FinaliseBackupId)) {
        $BackupId = $FinaliseBackupId
    } elseif ([string]::IsNullOrWhiteSpace($BackupId)) {
        $BackupId = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
    }
    $workspace = Join-Path $datasetBackupRoot ".$BackupId.partial"
    $finalBackup = Join-Path $datasetBackupRoot $BackupId

    if (-not (Test-Path -LiteralPath $filesRoot -PathType Container)) {
        throw "Selected Files root is unavailable: $filesRoot"
    }
    # Force one enumeration now so disconnected/misconfigured network roots fail before quiescence.
    [void](Get-ChildItem -LiteralPath $filesRoot -Force -ErrorAction Stop | Select-Object -First 1)

    $stagingInspection = Get-StagingInspection -FilesRoot $filesRoot
    $stagingPath = $stagingInspection.Path
    $stagingEntries = @($stagingInspection.Entries)
    $stagingDisposition = $stagingInspection.Disposition
    $stagingNote = $stagingInspection.Note

    $CurrentComposeArguments = Get-ComposeArguments -Mode $ModeName
    $dbContainerId = Get-ComposeServiceContainerId -Mode $ModeName -Service 'diaries-db'
    if ([string]::IsNullOrWhiteSpace($dbContainerId) -or -not (Test-ContainerRunning -ContainerId $dbContainerId)) {
        throw "The selected $ModeName diaries-db service is not running. Start that mode before taking a complete backup."
    }

    $dockerWriterStates = @()
    foreach ($consumer in $KnownConsumers) {
        if ($consumer -eq 'development-infrastructure') { continue }
        $running = Test-DockerResponderRunning -Mode $consumer
        $dockerWriterStates += [ordered]@{ mode = $consumer; service = 'diaries-responder'; wasRunning = $running; stoppedByCapture = $false }
    }

    $directState = [ordered]@{
        applicable = ($KnownConsumers -contains 'development-infrastructure')
        wasRunning = $false
        processIds = @()
        stoppedByCapture = $false
        restartCommand = 'diaries-responder\scripts\windows\run-responder.bat'
    }
    if ($directState.applicable) {
        $directWriters = Get-DirectWriterProcesses
        if ($directWriters.PotentialWriters.Count -gt 0) {
            $descriptions = @($directWriters.PotentialWriters | ForEach-Object { "PID=$($_.ProcessId) $($_.CommandLine)" }) -join [Environment]::NewLine
            throw "A migration/maintenance Java process may be writing the selected dataset. Stop it before backup:`n$descriptions"
        }
        $directState.wasRunning = ($directWriters.Responders.Count -gt 0)
        $directState.processIds = @($directWriters.Responders | ForEach-Object { [int]$_.ProcessId })
    }

    Write-Host ''
    Write-Host 'Diaries complete-dataset backup preflight'
    Write-Host "  Invoking mode:      $ModeName"
    Write-Host "  Logical dataset:    $datasetName"
    Write-Host "  Database data:      $databaseIdentity"
    Write-Host "  Files selector:     $($env:DIARIES_FILES_DIR)"
    Write-Host "  Files root:         $filesRoot"
    Write-Host "  Dataset sharing:    $sharing"
    Write-Host "  Known consumers:    $($KnownConsumers -join ', ')"
    Write-Host "  Database container: $dbContainerId (running)"
    Write-Host "  Staging:            $stagingDisposition/excluded ($($stagingEntries.Count) entries)"
    Write-Host "  Candidate:          $workspace"
    foreach ($writer in $dockerWriterStates) {
        Write-Host "  Writer:             docker:$($writer.mode)/$($writer.service) running=$($writer.wasRunning)"
    }
    if ($directState.applicable) {
        Write-Host "  Writer:             windows:direct-diaries-responder running=$($directState.wasRunning) pids=$($directState.processIds -join ',')"
    }

    if ($PreflightOnly) {
        Write-Host ''
        Write-Host 'PREFLIGHT OK: no writers were stopped and no backup workspace was created.'
        exit 0
    }

    if (-not [string]::IsNullOrWhiteSpace($FinaliseBackupId)) {
        $currentlyRunning = @($dockerWriterStates | Where-Object { [bool]$_.wasRunning })
        if ($directState.applicable -and $directState.wasRunning) { $currentlyRunning += $directState }
        if ($currentlyRunning.Count -gt 0) {
            throw 'Refusing Step-4 finalisation because an application writer is currently running. The Step-3 candidate must remain quiesced until promotion.'
        }
        $captureState = Read-CaptureState -Workspace $workspace
        Assert-CaptureStateMatchesCurrentDataset -State $captureState -ExpectedBackupId $BackupId -DatasetName $datasetName `
            -DatabaseIdentity $databaseIdentity -FilesSelector $env:DIARIES_FILES_DIR -FilesRoot $filesRoot
        Invoke-CompleteBackupFinalisation -Workspace $workspace -FinalBackup $finalBackup -State $captureState `
            -DbContainerId $dbContainerId -FilesRoot $filesRoot
        exit 0
    }

    if (Test-Path -LiteralPath $workspace) { throw "Incomplete backup workspace already exists: $workspace" }
    if (Test-Path -LiteralPath $finalBackup) { throw "Final backup directory already exists: $finalBackup" }
    New-Item -ItemType Directory -Path (Join-Path $workspace 'database') -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $workspace 'files') -Force | Out-Null

    $captureState = [ordered]@{
        schemaVersion = 1
        feature = '0033-FEAT'
        step = 3
        status = 'quiescing-writers'
        backupId = $BackupId
        logicalDataset = $datasetName
        invokingMode = $ModeName
        knownConsumers = @($KnownConsumers)
        startedAt = [DateTime]::UtcNow.ToString('o')
        captureCompletedAt = $null
        effectiveDatabaseDataDir = $databaseIdentity
        databaseName = $env:DIARIES_DB_NAME
        effectiveFilesDir = $env:DIARIES_FILES_DIR
        resolvedPhysicalFilesRoot = $filesRoot
        source = [ordered]@{ gitCommit = Get-GitCommit }
        database = [ordered]@{ composeService = 'diaries-db'; containerId = $dbContainerId; imageRowCount = $null; cataloguedFileCount = $null }
        staging = [ordered]@{ relativePath = $StagingName; disposition = $stagingDisposition; entryCount = $stagingEntries.Count; snapshotIncluded = $false; note = $stagingNote }
        writers = [ordered]@{ dockerResponders = @($dockerWriterStates); directResponder = $directState; quiesced = $false }
        components = [ordered]@{ customDump = 'database/diaries.dump'; sqlDump = 'database/diaries.sql'; filesSnapshot = 'files' }
        fileCopy = [ordered]@{ method = 'robocopy'; fileAttributes = 'DAT'; directoryAttributes = 'DAT'; stagingExcluded = $true }
        finalisation = [ordered]@{ requiredStep = 4; finalDirectory = $finalBackup; priorWriterStateMustBeRestoredOnlyAfterSuccess = $true }
        failure = $null
    }
    Write-CaptureState -State $captureState -Workspace $workspace

    # Quiesce every responder that can consume this effective pair. PostgreSQL remains running.
    foreach ($writer in $captureState.writers.dockerResponders) {
        if ([bool]$writer.wasRunning) {
            Stop-DockerResponder -Mode ([string]$writer.mode)
            $writer.stoppedByCapture = $true
        }
    }
    if ($directState.applicable -and $directState.wasRunning) {
        foreach ($pidValue in $directState.processIds) {
            Stop-Process -Id ([int]$pidValue) -ErrorAction Stop
        }
        $directState.stoppedByCapture = $true
    }
    Wait-ForWriterStop
    $captureState.writers.quiesced = $true

    # Close the preflight/quiescence race: inspect staging again after every application writer is stopped.
    $stagingInspection = Get-StagingInspection -FilesRoot $filesRoot
    $captureState.staging.disposition = $stagingInspection.Disposition
    $captureState.staging.entryCount = $stagingInspection.EntryCount
    $captureState.staging.note = $stagingInspection.Note
    $captureState.status = 'writers-quiesced'
    Write-CaptureState -State $captureState -Workspace $workspace

    # Capture database counts and both dump formats while all application writers are stopped.
    $imageCount = Invoke-DatabaseScalar -Sql 'SELECT count(*) FROM public.image;'
    $cataloguedCount = Invoke-DatabaseScalar -Sql "SELECT count(*) FROM public.image WHERE relative_path IS NOT NULL AND btrim(relative_path) <> '';"
    $captureState.database.imageRowCount = $imageCount
    $captureState.database.cataloguedFileCount = $cataloguedCount

    $token = [Guid]::NewGuid().ToString('N')
    $containerDump = "/tmp/diaries-0033-$token.dump"
    $containerSql = "/tmp/diaries-0033-$token.sql"
    Invoke-PostgresDumpToContainer -Format custom -ContainerPath $containerDump
    Copy-ContainerFileToHost -ContainerId $dbContainerId -ContainerPath $containerDump -Destination (Join-Path $workspace 'database\diaries.dump')
    Invoke-PostgresDumpToContainer -Format plain -ContainerPath $containerSql
    Copy-ContainerFileToHost -ContainerId $dbContainerId -ContainerPath $containerSql -Destination (Join-Path $workspace 'database\diaries.sql')
    Remove-ContainerTemporaryFile -ContainerId $dbContainerId -ContainerPath $containerDump
    $containerDump = $null
    Remove-ContainerTemporaryFile -ContainerId $dbContainerId -ContainerPath $containerSql
    $containerSql = $null

    Copy-DurableFiles -Source $filesRoot -Destination (Join-Path $workspace 'files')

    $captureState.status = 'captured-awaiting-step4-finalisation'
    $captureState.captureCompletedAt = [DateTime]::UtcNow.ToString('o')
    Write-CaptureState -State $captureState -Workspace $workspace

    Write-Host ''
    Write-Host 'STEP 3 CAPTURE COMPLETE; proceeding directly to Step 4 verification/finalisation while writers remain quiesced.'
    Write-Host "  Incomplete workspace: $workspace"
    Write-Host "  Database custom dump: database\diaries.dump"
    Write-Host "  Database SQL dump:    database\diaries.sql"
    Write-Host "  Durable Files copy:   files\"
    Write-Host "  Image rows:           $imageCount"
    Write-Host "  Catalogued files:     $cataloguedCount"

    Invoke-CompleteBackupFinalisation -Workspace $workspace -FinalBackup $finalBackup -State $captureState `
        -DbContainerId $dbContainerId -FilesRoot $filesRoot
    exit 0
}
catch {
    $message = $_.Exception.Message
    if ($workspace -and (Test-Path -LiteralPath $workspace -PathType Container) -and $null -ne $captureState) {
        try {
            $failureStatus = if ([string]$captureState.status -in @('captured-awaiting-step4-finalisation','step4-verified-awaiting-promotion','finalisation-failed-incomplete')) { 'finalisation-failed-incomplete' } else { 'failed-incomplete' }
            Set-StateProperty -Target $captureState -Name 'status' -Value $failureStatus
            Set-StateProperty -Target $captureState -Name 'failure' -Value ([ordered]@{ at = [DateTime]::UtcNow.ToString('o'); message = $message })
            Write-CaptureState -State $captureState -Workspace $workspace
        } catch { }
    }
    Write-Error $message
    if ($workspace -and (Test-Path -LiteralPath $workspace -PathType Container)) {
        Write-Host "Incomplete workspace retained for diagnosis: $workspace" -ForegroundColor Yellow
    }
    Write-Host 'Any writer stopped by this operation is intentionally left stopped after failure.' -ForegroundColor Yellow
    exit 1
}
finally {
    try { Remove-ContainerTemporaryFile -ContainerId $dbContainerId -ContainerPath $containerDump } catch { }
    try { Remove-ContainerTemporaryFile -ContainerId $dbContainerId -ContainerPath $containerSql } catch { }
}
