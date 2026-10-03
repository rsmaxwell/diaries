param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('development-infrastructure', 'local-docker-build', 'local-published-smoke')]
    [string]$ModeName,

    [Parameter(Mandatory = $true)]
    [string]$ModeEnvironmentFile,

    [Parameter(Mandatory = $true)]
    [string]$LocalEnvironmentFile
)

$ErrorActionPreference = 'Stop'

$DatabaseKey = 'DIARIES_DB_DATA_DIR'
$FilesKey = 'DIARIES_FILES_DIR'

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
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('#')) {
            continue
        }

        $equals = $line.IndexOf('=')
        if ($equals -lt 1) {
            continue
        }

        $key = $line.Substring(0, $equals).Trim()
        $value = $line.Substring($equals + 1).Trim()
        if ([string]::IsNullOrWhiteSpace($key)) {
            continue
        }

        $values[$key] = $value
        [void]$present.Add($key)
    }

    [pscustomobject]@{
        Values = $values
        Present = $present
    }
}

function Require-Value {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Source
    )

    if (-not $Values.ContainsKey($Key) -or [string]::IsNullOrWhiteSpace([string]$Values[$Key])) {
        throw "$Source must define a non-empty $Key."
    }
}

try {
    $mode = Read-DotEnvFile -Path $ModeEnvironmentFile
    $local = Read-DotEnvFile -Path $LocalEnvironmentFile

    Require-Value -Values $mode.Values -Key $DatabaseKey -Source $ModeEnvironmentFile
    Require-Value -Values $mode.Values -Key $FilesKey -Source $ModeEnvironmentFile

    $databaseOverridden = $local.Present.Contains($DatabaseKey)
    $filesOverridden = $local.Present.Contains($FilesKey)

    if ($databaseOverridden -xor $filesOverridden) {
        $missing = if ($databaseOverridden) { $FilesKey } else { $DatabaseKey }
        $present = if ($databaseOverridden) { $DatabaseKey } else { $FilesKey }
        throw "Dataset override mismatch in ${LocalEnvironmentFile}: $present is overridden but $missing is not. Database and mutable Files selectors must be overridden together."
    }

    $effectiveDatabase = if ($databaseOverridden) {
        [string]$local.Values[$DatabaseKey]
    }
    else {
        [string]$mode.Values[$DatabaseKey]
    }

    $effectiveFiles = if ($filesOverridden) {
        [string]$local.Values[$FilesKey]
    }
    else {
        [string]$mode.Values[$FilesKey]
    }

    if ([string]::IsNullOrWhiteSpace($effectiveDatabase)) {
        throw "Effective $DatabaseKey is empty after applying $ModeEnvironmentFile and $LocalEnvironmentFile."
    }
    if ([string]::IsNullOrWhiteSpace($effectiveFiles)) {
        throw "Effective $FilesKey is empty after applying $ModeEnvironmentFile and $LocalEnvironmentFile."
    }

    if ($effectiveFiles -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
        throw "Effective $FilesKey '$effectiveFiles' is not a valid Files leaf-directory selector."
    }

    # 'files' is the production mutable root frozen by 0031 Step 2. Local modes
    # must never select it, even when both local override keys are present.
    if ($effectiveFiles -eq 'files') {
        throw "Unsafe local Files selection: DIARIES_FILES_DIR=files is reserved for the production dataset. Select the matching local Files root instead."
    }

    # For the approved 0031 local datasets the database leaf gives us a reliable
    # path-based pairing check. Unknown/custom database leaves are allowed only
    # after passing the paired-override rule above; no database identity is ever
    # inferred inside responder Java.
    $normalisedDatabase = $effectiveDatabase.Replace('\', '/').TrimEnd('/')
    $databaseLeaf = ($normalisedDatabase -split '/')[-1]
    $approvedFilesByDatabaseLeaf = @{
        'development-infrastructure' = 'files-development-infrastructure'
        'local-docker-build' = 'files-local-docker-build'
        'local-published-smoke' = 'files-local-published-smoke'
        'common' = 'files-development-common'
    }

    if ($approvedFilesByDatabaseLeaf.ContainsKey($databaseLeaf)) {
        $expectedFiles = [string]$approvedFilesByDatabaseLeaf[$databaseLeaf]
        if ($effectiveFiles -ne $expectedFiles) {
            throw "Dataset pair mismatch for database '$effectiveDatabase': expected DIARIES_FILES_DIR=$expectedFiles but found '$effectiveFiles'."
        }
    }

    Write-Host "Validated Diaries dataset pair for ${ModeName}:"
    Write-Host "  Database data: $effectiveDatabase"
    Write-Host "  Files dir:     $effectiveFiles"
    if ($databaseOverridden) {
        Write-Host "  Source:        paired local.env override"
    }
    else {
        Write-Host "  Source:        isolated committed mode defaults"
    }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
