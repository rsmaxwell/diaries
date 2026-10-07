Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-DiariesProjectRoot {
    param([string]$StartPath = $PSScriptRoot)
    $current = [System.IO.Path]::GetFullPath($StartPath)
    if (Test-Path -LiteralPath $current -PathType Leaf) { $current = Split-Path -Parent $current }
    while ($true) {
        $required = @('diaries-client','diaries-responder','diaries-web','change-control')
        $ok = $true
        foreach ($name in $required) {
            if (-not (Test-Path -LiteralPath (Join-Path $current $name) -PathType Container)) { $ok = $false; break }
        }
        if ($ok) { return $current }
        $parent = Split-Path -Parent $current
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
            throw "Could not locate the Diaries project root from $StartPath"
        }
        $current = $parent
    }
}

function Get-Step15BuildRoot {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    Join-Path $ProjectRoot 'build\0027-step15'
}

function Get-CurrentStep15RunDirectory {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $buildRoot = Get-Step15BuildRoot -ProjectRoot $ProjectRoot
    $marker = Join-Path $buildRoot 'current-run.txt'
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        throw "No Step 15 run is active. Run step15-begin.ps1 first: $marker"
    }
    $runId = (Get-Content -LiteralPath $marker -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($runId)) { throw "Step 15 run marker is empty: $marker" }
    $runDirectory = Join-Path (Join-Path $buildRoot 'runs') $runId
    if (-not (Test-Path -LiteralPath $runDirectory -PathType Container)) {
        throw "Step 15 run directory does not exist: $runDirectory"
    }
    $runDirectory
}

function Find-PassedStep14Summary {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot,[string]$Step14Summary)
    if (-not [string]::IsNullOrWhiteSpace($Step14Summary)) {
        $candidate = if ([System.IO.Path]::IsPathRooted($Step14Summary)) { $Step14Summary } else { Join-Path $ProjectRoot $Step14Summary }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Step 14 summary not found: $candidate" }
        $json = Get-Content -LiteralPath $candidate -Raw | ConvertFrom-Json
        if ([string]$json.status -ne 'PASSED') { throw "Step 14 summary is not PASSED: $candidate" }
        return (Resolve-Path -LiteralPath $candidate).Path
    }

    $root = Join-Path $ProjectRoot 'build\0027-step14\runs'
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        throw "Step 14 run directory not found: $root"
    }
    $candidates = Get-ChildItem -LiteralPath $root -Directory | Sort-Object Name -Descending
    foreach ($run in $candidates) {
        $candidate = Join-Path $run.FullName 'step14-final-summary.json'
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        try {
            $json = Get-Content -LiteralPath $candidate -Raw | ConvertFrom-Json
            if ([string]$json.status -eq 'PASSED') { return $candidate }
        } catch { }
    }
    throw 'No PASSED Step 14 final summary was found. Step 15 must not perform production actions until Step 14 is closed.'
}

function Write-Utf8NoBom {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Text)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Text,$utf8)
}

function Get-GitIdentityLines {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Label)
    $lines = New-Object System.Collections.Generic.List[string]
    try {
        $commit = (& git -C $Path rev-parse HEAD 2>$null) -join ''
        if ([string]::IsNullOrWhiteSpace($commit)) { $commit = '<unavailable>' }
        $lines.Add("$Label.commit=$commit")
        $status = & git -C $Path status --short 2>$null
        $lines.Add("$Label.status=" + ($(if($status){'dirty'}else{'clean'})))
    } catch {
        $lines.Add("$Label.commit=<unavailable>")
        $lines.Add("$Label.status=<unavailable>")
    }
    $lines
}

function Assert-SafeRemotePath {
    param([Parameter(Mandatory=$true)][string]$Path)
    if ($Path -notmatch '^/[A-Za-z0-9._/-]+$') { throw "Remote path contains unsupported shell characters: $Path" }
    $Path.TrimEnd('/')
}

function Invoke-Step15Ssh {
    param(
        [Parameter(Mandatory=$true)][string]$HostName,
        [Parameter(Mandatory=$true)][string]$Command,
        [switch]$AllowFailure
    )
    # Send the remote command over stdin rather than as an ssh command-line argument.
    # This preserves nested shell quoting in Docker --format templates and SQL snippets
    # when the caller is Windows PowerShell/OpenSSH. Windows PowerShell appends CRLF
    # when piping a string to a native command, so terminate the payload with a comment;
    # any trailing carriage return then belongs to the comment instead of the final token.
    $normalizedCommand = $Command -replace "`r`n", "`n"
    $payload = $normalizedCommand + "`n# step15-ssh-eof"

    # Native stderr is represented as ErrorRecord objects by Windows PowerShell 5.1.
    # Capture those records and decide success from ssh's actual exit code rather than
    # allowing the script-wide ErrorActionPreference=Stop to abort prematurely.
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $rawResult = @($payload | & ssh $HostName bash -s 2>&1)
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $result = @(foreach ($item in $rawResult) {
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            $item.Exception.Message
        } else {
            [string]$item
        }
    })

    if ($code -ne 0 -and -not $AllowFailure) {
        throw "Remote command failed on $HostName (exit $code): $Command`n$($result -join [Environment]::NewLine)"
    }
    [pscustomobject]@{ ExitCode = $code; Lines = @($result) }
}
