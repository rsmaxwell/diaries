param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('development-infrastructure', 'local-docker-build', 'local-published-smoke')]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [string]$ResponderLog
)

$ErrorActionPreference = 'Stop'
$ProjectDir = [System.IO.Path]::GetFullPath($ProjectDir)
$FeatureDir = Join-Path $ProjectDir 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment'
$EvidenceRoot = Join-Path $FeatureDir 'evidence\Step 11\runtime'
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$EvidenceDir = Join-Path $EvidenceRoot ("{0}-{1}" -f $Mode, $Timestamp)
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$TranscriptPath = Join-Path $EvidenceDir 'STEP11-CONSOLE.txt'
$transcriptStarted = $false
try {
    Start-Transcript -Path $TranscriptPath -Force | Out-Null
    $transcriptStarted = $true
} catch {
    # Continue even on hosts where transcription is unavailable; the structured
    # report and individual evidence files are still produced.
}

$report = [ordered]@{
    feature = '0031-FEAT'
    step = 11
    mode = $Mode
    capturedAt = (Get-Date).ToString('o')
    status = 'FAIL'
    effectiveDatabaseDataDir = $null
    databaseBacking = $null
    filesSelector = $null
    dockerFilesPath = $null
    filesBacking = $null
    diaryBacking = $null
    databaseContainer = $null
    responderContainer = $null
    imageRelativePathChecked = $null
    diaryRelativePathChecked = $null
    publicFilesContext = '/files'
    publicDiariesContext = '/diaries'
    responderLogCaptured = $false
    checks = @()
    error = $null
}

function Add-Check {
    param([string]$Text)
    $script:report.checks += $Text
    Write-Host "PASS: $Text"
}

function Read-DotEnv {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Environment file not found: $Path"
    }
    $values = @{}
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = [string]$raw
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('#')) { continue }
        $equals = $line.IndexOf('=')
        if ($equals -lt 1) { continue }
        $key = $line.Substring(0, $equals).Trim()
        $value = $line.Substring($equals + 1).Trim()
        if (-not [string]::IsNullOrWhiteSpace($key)) { $values[$key] = $value }
    }
    return $values
}

function Merge-Environment {
    param([hashtable]$Base, [hashtable]$Override)
    $result = @{}
    foreach ($key in $Base.Keys) { $result[$key] = $Base[$key] }
    foreach ($key in $Override.Keys) { $result[$key] = $Override[$key] }
    return $result
}

function Redact-Text {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $result = [string]$Text
    if ($null -ne $script:effective) {
        foreach ($key in $script:effective.Keys) {
            if ([string]$key -match '(?i)(password|secret|token|credential|passphrase|api.?key)') {
                $value = [string]$script:effective[$key]
                if (-not [string]::IsNullOrEmpty($value)) { $result = $result.Replace($value, '<redacted>') }
            }
        }
    }
    $result = [regex]::Replace($result, '(?im)(password\s*[=:]\s*)[^,;\s]+', '$1<redacted>')
    return $result
}

function Get-ValueOrDefault {
    param([hashtable]$Values, [string]$Key, [string]$Default)
    if ($Values.ContainsKey($Key) -and -not [string]::IsNullOrWhiteSpace([string]$Values[$Key])) {
        return [string]$Values[$Key]
    }
    return $Default
}

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$StderrFile
    )
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        if ($StderrFile) {
            $stdout = & $FilePath @Arguments 2> $StderrFile
        } else {
            $stdout = & $FilePath @Arguments 2>&1
        }
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldPreference
    }
    [pscustomobject]@{
        ExitCode = $exitCode
        Stdout = (($stdout | ForEach-Object { [string]$_ }) -join [Environment]::NewLine)
    }
}

function Convert-ToRedactedValue {
    param($Value, [string]$PropertyName = '')

    if ($PropertyName -match '(?i)(password|secret|token|credential|passphrase|api.?key)') {
        return '<redacted>'
    }
    if ($null -eq $Value) { return $null }
    if ($Value -is [string]) {
        $text = [string]$Value
        $text = [regex]::Replace($text, '(?i)(password=)[^,;\s]+', '$1<redacted>')
        return $text
    }
    if ($Value -is [ValueType]) { return $Value }
    if ($Value -is [System.Collections.IDictionary]) {
        $map = [ordered]@{}
        foreach ($key in $Value.Keys) {
            $map[[string]$key] = Convert-ToRedactedValue -Value $Value[$key] -PropertyName ([string]$key)
        }
        return $map
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        $items = @()
        foreach ($item in $Value) { $items += ,(Convert-ToRedactedValue -Value $item) }
        return $items
    }

    $object = [ordered]@{}
    foreach ($property in $Value.PSObject.Properties) {
        $object[$property.Name] = Convert-ToRedactedValue -Value $property.Value -PropertyName $property.Name
    }
    return $object
}

function Save-Json {
    param($Value, [string]$Path)
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Encode-RelativeUrlPath {
    param([string]$RelativePath)
    $segments = @()
    foreach ($segment in ($RelativePath -split '/')) {
        $segments += [Uri]::EscapeDataString($segment)
    }
    return ($segments -join '/')
}

function Assert-HttpHead {
    param([string]$Url, [string]$Description)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -UseBasicParsing -TimeoutSec 15
        if ([int]$response.StatusCode -lt 200 -or [int]$response.StatusCode -ge 400) {
            throw "HTTP status $($response.StatusCode)"
        }
        Add-Check "$Description returned HTTP $($response.StatusCode)"
    } catch {
        throw "$Description failed for $Url : $($_.Exception.Message)"
    }
}

function Get-FirstImageRelativePath {
    param([string]$Container, [string]$DatabaseUser, [string]$DatabaseName)
    $result = Invoke-NativeCapture -FilePath 'docker' -Arguments @(
        'exec', $Container, 'psql', '-U', $DatabaseUser, '-d', $DatabaseName,
        '-At', '-c', 'SELECT relative_path FROM public.image ORDER BY id LIMIT 1;'
    )
    if ($result.ExitCode -ne 0) { throw "Could not query first Image relative_path from $Container.`n$($result.Stdout)" }
    $relative = $result.Stdout.Trim()
    if ([string]::IsNullOrWhiteSpace($relative)) { throw 'The Image catalogue contains no row to use for the read-only static-file check.' }
    return $relative
}

function Get-FirstContainerFileRelativePath {
    param([string]$Container, [string]$Root)
    $command = "find '$Root' -type f -print | sed 's#^$Root/##' | head -n 1"
    $result = Invoke-NativeCapture -FilePath 'docker' -Arguments @('exec', $Container, 'sh', '-lc', $command)
    if ($result.ExitCode -ne 0) { throw "Could not list $Root in $Container.`n$($result.Stdout)" }
    return $result.Stdout.Trim()
}

try {
    Write-Host "0031 Step 11 runtime capture: $Mode"
    Write-Host "Evidence: $EvidenceDir"

    $modeEnvPath = Join-Path $ProjectDir ("config\environments\{0}.env" -f $Mode)
    $localEnvPath = Join-Path $ProjectDir 'config\environments\local.env'
    $script:effective = Merge-Environment -Base (Read-DotEnv $modeEnvPath) -Override (Read-DotEnv $localEnvPath)
    $effective = $script:effective

    $dbData = Get-ValueOrDefault -Values $effective -Key 'DIARIES_DB_DATA_DIR' -Default ''
    $filesDir = Get-ValueOrDefault -Values $effective -Key 'DIARIES_FILES_DIR' -Default ''
    if ([string]::IsNullOrWhiteSpace($dbData) -or [string]::IsNullOrWhiteSpace($filesDir)) {
        throw 'Effective database/Files selectors are incomplete.'
    }
    if ($filesDir -eq 'files') { throw 'Local Step 11 verification refuses the production Files selector.' }

    if ([System.IO.Path]::IsPathRooted($dbData)) {
        $resolvedDbData = [System.IO.Path]::GetFullPath($dbData)
    } else {
        $resolvedDbData = [System.IO.Path]::GetFullPath((Join-Path $ProjectDir $dbData))
    }
    $report.effectiveDatabaseDataDir = $resolvedDbData
    $report.filesSelector = $filesDir
    Add-Check "effective Files selector is non-production: $filesDir"

    $containerNames = @{
        'development-infrastructure' = @{ Database = 'diaries-development-db'; Responder = $null }
        'local-docker-build' = @{ Database = 'diaries-local-db'; Responder = 'diaries-local-responder' }
        'local-published-smoke' = @{ Database = 'diaries-published-smoke-db'; Responder = 'diaries-published-smoke-responder' }
    }
    $report.databaseContainer = $containerNames[$Mode].Database
    $report.responderContainer = $containerNames[$Mode].Responder

    $composeFile = switch ($Mode) {
        'development-infrastructure' { Join-Path $ProjectDir 'compose.development-infrastructure.yaml' }
        'local-docker-build' { Join-Path $ProjectDir 'compose.local-docker-build.yaml' }
        'local-published-smoke' { Join-Path $ProjectDir 'compose.local-published-smoke.yaml' }
    }
    $composeStderr = Join-Path $EvidenceDir 'COMPOSE-CONFIG-STDERR.txt'
    $composeResult = Invoke-NativeCapture -FilePath 'docker' -Arguments @(
        'compose', '-f', $composeFile, '--env-file', $modeEnvPath, '--env-file', $localEnvPath,
        'config', '--format', 'json'
    ) -StderrFile $composeStderr
    if ($composeResult.ExitCode -ne 0) { throw "docker compose config failed.`n$($composeResult.Stdout)" }
    $compose = $composeResult.Stdout | ConvertFrom-Json
    Save-Json -Value (Convert-ToRedactedValue -Value $compose) -Path (Join-Path $EvidenceDir 'COMPOSE-RENDERED-REDACTED.json')

    $databaseService = $compose.services.'diaries-db'
    if ($null -eq $databaseService) { throw 'Rendered Compose config is missing diaries-db.' }
    $dbUser = [string]$databaseService.environment.POSTGRES_USER
    $dbName = [string]$databaseService.environment.POSTGRES_DB
    if ([string]::IsNullOrWhiteSpace($dbUser) -or [string]::IsNullOrWhiteSpace($dbName)) {
        throw 'Rendered Compose database environment does not contain POSTGRES_USER and POSTGRES_DB.'
    }
    $dbMount = @($databaseService.volumes | Where-Object { $_.target -eq '/var/lib/postgresql' })
    if ($dbMount.Count -ne 1) { throw 'Rendered Compose config does not contain exactly one /var/lib/postgresql mount.' }
    $renderedDbSource = [System.IO.Path]::GetFullPath([string]$dbMount[0].source)
    $report.databaseBacking = $renderedDbSource
    if (-not $renderedDbSource.Equals($resolvedDbData, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Rendered database mount '$renderedDbSource' does not match effective database data directory '$resolvedDbData'."
    }
    Add-Check 'rendered Compose database mount matches the effective database data directory'

    if ($Mode -eq 'development-infrastructure') {
        $prepare = Join-Path $ProjectDir 'scripts\windows\development-infrastructure\prepare-responder-config.bat'
        $prepareOutput = Invoke-NativeCapture -FilePath 'cmd.exe' -Arguments @('/d', '/c', ('call "' + $prepare + '"'))
        (Redact-Text $prepareOutput.Stdout) | Set-Content -LiteralPath (Join-Path $EvidenceDir 'PREPARE-RESPONDER-CONFIG.txt') -Encoding UTF8
        if ($prepareOutput.ExitCode -ne 0) { throw "prepare-responder-config.bat failed.`n$($prepareOutput.Stdout)" }

        $effectiveConfigPath = Join-Path $ProjectDir 'build\development-infrastructure\responder.effective.json'
        if (-not (Test-Path -LiteralPath $effectiveConfigPath -PathType Leaf)) {
            throw "Generated responder configuration not found: $effectiveConfigPath"
        }
        $config = Get-Content -LiteralPath $effectiveConfigPath -Raw | ConvertFrom-Json
        $redactedConfig = Convert-ToRedactedValue -Value $config
        Save-Json -Value $redactedConfig -Path (Join-Path $EvidenceDir 'RESPONDER-EFFECTIVE-REDACTED.json')

        if ([string]$config.diaries.files -ne $filesDir) {
            throw "Generated diaries.files '$($config.diaries.files)' does not match effective DIARIES_FILES_DIR '$filesDir'."
        }
        $filesRoot = [System.IO.Path]::GetFullPath((Join-Path ([string]$config.diaries.root) ([string]$config.diaries.files)))
        $diaryRoot = [System.IO.Path]::GetFullPath((Join-Path ([string]$config.diaries.root) ([string]$config.diaries.diaries)))
        $report.filesBacking = $filesRoot
        $report.diaryBacking = $diaryRoot
        if (-not (Test-Path -LiteralPath $filesRoot -PathType Container)) { throw "Effective direct Files root does not exist: $filesRoot" }
        if (-not (Test-Path -LiteralPath $diaryRoot -PathType Container)) { throw "Shared direct diary root does not exist: $diaryRoot" }
        Add-Check "generated direct responder config resolves diaries.files to $filesDir"
        Add-Check 'direct Files root exists'
        Add-Check 'shared diary root exists'

        Get-ChildItem -LiteralPath $filesRoot -File -Recurse | Select-Object -First 20 FullName,Length |
            Format-Table -AutoSize | Out-String | Set-Content -LiteralPath (Join-Path $EvidenceDir 'FILES-LIST.txt') -Encoding UTF8

        if ($ResponderLog) {
            $resolvedLog = [System.IO.Path]::GetFullPath($ResponderLog)
            if (-not (Test-Path -LiteralPath $resolvedLog -PathType Leaf)) { throw "Responder log not found: $resolvedLog" }
            (Redact-Text (Get-Content -LiteralPath $resolvedLog -Raw)) | Set-Content -LiteralPath (Join-Path $EvidenceDir 'RESPONDER-STARTUP-LOG.txt') -Encoding UTF8
            $report.responderLogCaptured = $true
            Add-Check 'direct responder startup log captured'
        } else {
            'Direct responder log was not supplied. Re-run capture-local-mode.bat with the log path before Step 11 close-out.' |
                Set-Content -LiteralPath (Join-Path $EvidenceDir 'RESPONDER-STARTUP-LOG-NOT-CAPTURED.txt') -Encoding UTF8
        }

        $imageRelative = Get-FirstImageRelativePath -Container $report.databaseContainer -DatabaseUser $dbUser -DatabaseName $dbName
        $report.imageRelativePathChecked = $imageRelative
        $imagePhysical = Join-Path $filesRoot ($imageRelative.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
        if (-not (Test-Path -LiteralPath $imagePhysical -PathType Leaf)) { throw "Catalogued Image file is missing from effective Files root: $imageRelative" }
        Add-Check 'catalogued Image path exists under the effective direct Files root'

        $filesUrl = 'http://127.0.0.1:8081/files/' + (Encode-RelativeUrlPath $imageRelative)
        Assert-HttpHead -Url $filesUrl -Description 'stable /files static route'

        $diaryFile = Get-ChildItem -LiteralPath $diaryRoot -File -Recurse | Select-Object -First 1
        if ($null -ne $diaryFile) {
            $diaryRelative = $diaryFile.FullName.Substring($diaryRoot.Length).TrimStart([char[]]'\/').Replace('\','/')
            $report.diaryRelativePathChecked = $diaryRelative
            $diaryUrl = 'http://127.0.0.1:8081/diaries/' + (Encode-RelativeUrlPath $diaryRelative)
            Assert-HttpHead -Url $diaryUrl -Description 'shared /diaries static route'
        } else {
            throw 'Shared diary source tree contains no file for the read-only HTTP check.'
        }
    }
    else {
        $responderService = $compose.services.'diaries-responder'
        if ($null -eq $responderService) { throw 'Rendered Compose config is missing diaries-responder.' }
        $filesMount = @($responderService.volumes | Where-Object { $_.target -eq '/data/files' })
        $diaryMount = @($responderService.volumes | Where-Object { $_.target -eq '/data/diaries' })
        if ($filesMount.Count -ne 1 -or $diaryMount.Count -ne 1) {
            throw 'Rendered Compose mounts do not contain exactly one Files and diary mount.'
        }
        $expectedFilesSubpath = ((Get-ValueOrDefault $effective 'DIARIES_NAS_CONTENT_PATH' '')).TrimEnd([char[]]'\/') + '/' + $filesDir
        $expectedDiarySubpath = ((Get-ValueOrDefault $effective 'DIARIES_NAS_CONTENT_PATH' '')).TrimEnd([char[]]'\/') + '/diaries'
        $actualFilesSubpath = [string]$filesMount[0].volume.subpath
        $actualDiarySubpath = [string]$diaryMount[0].volume.subpath
        if ($actualFilesSubpath.Replace('\','/') -ne $expectedFilesSubpath.Replace('\','/')) {
            throw "Rendered /data/files subpath '$actualFilesSubpath' does not match '$expectedFilesSubpath'."
        }
        if ($actualDiarySubpath.Replace('\','/') -ne $expectedDiarySubpath.Replace('\','/')) {
            throw "Rendered /data/diaries subpath '$actualDiarySubpath' does not match '$expectedDiarySubpath'."
        }
        if (-not [bool]$diaryMount[0].read_only) { throw 'Rendered /data/diaries mount is not read-only.' }
        $report.dockerFilesPath = '/data/files'
        $report.filesBacking = $actualFilesSubpath
        $report.diaryBacking = $actualDiarySubpath
        Add-Check "rendered Compose binds selected NAS subpath to /data/files"
        Add-Check 'rendered Compose keeps the shared /data/diaries mount read-only'

        $inspectStderr = Join-Path $EvidenceDir 'RESPONDER-INSPECT-STDERR.txt'
        $inspectResult = Invoke-NativeCapture -FilePath 'docker' -Arguments @('inspect', $report.responderContainer) -StderrFile $inspectStderr
        if ($inspectResult.ExitCode -ne 0) { throw "Responder container is not available: $($report.responderContainer)" }
        $inspect = $inspectResult.Stdout | ConvertFrom-Json
        if (-not [bool]$inspect[0].State.Running) { throw "Responder container is not running: $($report.responderContainer)" }
        $safeMounts = @($inspect[0].Mounts | ForEach-Object {
            [ordered]@{ Type=$_.Type; Name=$_.Name; Source=$_.Source; Destination=$_.Destination; RW=$_.RW }
        })
        Save-Json -Value $safeMounts -Path (Join-Path $EvidenceDir 'RESPONDER-MOUNTS.json')
        if (-not (@($inspect[0].Mounts | Where-Object { $_.Destination -eq '/data/files' -and $_.RW }).Count -eq 1)) {
            throw 'Runtime responder mount inspection did not show one writable /data/files mount.'
        }
        if (-not (@($inspect[0].Mounts | Where-Object { $_.Destination -eq '/data/diaries' -and -not $_.RW }).Count -eq 1)) {
            throw 'Runtime responder mount inspection did not show one read-only /data/diaries mount.'
        }
        Add-Check 'runtime mount inspection shows /data/files and read-only /data/diaries'

        $filesList = Invoke-NativeCapture -FilePath 'docker' -Arguments @('exec', $report.responderContainer, 'sh', '-lc', "find /data/files -type f -print | head -n 20")
        if ($filesList.ExitCode -ne 0) { throw 'Could not list /data/files inside the responder container.' }
        $filesList.Stdout | Set-Content -LiteralPath (Join-Path $EvidenceDir 'FILES-LIST.txt') -Encoding UTF8
        Add-Check 'read-only file listing succeeded inside /data/files'

        $logs = Invoke-NativeCapture -FilePath 'docker' -Arguments @('logs', '--tail', '300', $report.responderContainer)
        (Redact-Text $logs.Stdout) | Set-Content -LiteralPath (Join-Path $EvidenceDir 'RESPONDER-STARTUP-LOG.txt') -Encoding UTF8
        if ($logs.ExitCode -ne 0) { throw 'Could not capture responder logs.' }
        $report.responderLogCaptured = $true
        Add-Check 'responder startup/runtime log captured'

        $imageRelative = Get-FirstImageRelativePath -Container $report.databaseContainer -DatabaseUser $dbUser -DatabaseName $dbName
        $report.imageRelativePathChecked = $imageRelative
        $fileCheck = Invoke-NativeCapture -FilePath 'docker' -Arguments @('exec', $report.responderContainer, 'test', '-f', ('/data/files/' + $imageRelative))
        if ($fileCheck.ExitCode -ne 0) { throw "Catalogued Image is absent beneath /data/files: $imageRelative" }
        Add-Check 'catalogued Image path exists beneath runtime /data/files'

        $portKey = if ($Mode -eq 'local-published-smoke') { 'DIARIES_RESPONDER_HTTP_HOST_PORT' } else { 'DIARIES_RESPONDER_PORT' }
        $httpPort = Get-ValueOrDefault -Values $effective -Key $portKey -Default '8081'
        $filesUrl = "http://127.0.0.1:$httpPort/files/" + (Encode-RelativeUrlPath $imageRelative)
        Assert-HttpHead -Url $filesUrl -Description 'stable /files static route'

        $diaryRelative = Get-FirstContainerFileRelativePath -Container $report.responderContainer -Root '/data/diaries'
        if ([string]::IsNullOrWhiteSpace($diaryRelative)) { throw 'Shared /data/diaries tree contains no file for the read-only HTTP check.' }
        $report.diaryRelativePathChecked = $diaryRelative
        $diaryUrl = "http://127.0.0.1:$httpPort/diaries/" + (Encode-RelativeUrlPath $diaryRelative)
        Assert-HttpHead -Url $diaryUrl -Description 'shared /diaries static route'
    }

    $pathsText = @(
        "Mode: $Mode",
        "Database data: $($report.effectiveDatabaseDataDir)",
        "Database backing: $($report.databaseBacking)",
        "Files selector: $($report.filesSelector)",
        "Files backing: $($report.filesBacking)",
        "Runtime Files path: $($report.dockerFilesPath)",
        "Diary backing: $($report.diaryBacking)",
        "Public Files context: $($report.publicFilesContext)",
        "Public Diaries context: $($report.publicDiariesContext)"
    ) -join [Environment]::NewLine
    $pathsText | Set-Content -LiteralPath (Join-Path $EvidenceDir 'EFFECTIVE-PATHS.txt') -Encoding UTF8

    $report.status = 'PASS'
    Add-Check 'Step 11 mode capture completed without upload/delete/rename operations'
}
catch {
    $report.error = $_.Exception.Message
    [Console]::Error.WriteLine('FAIL: ' + $_.Exception.Message)
}
finally {
    Save-Json -Value $report -Path (Join-Path $EvidenceDir 'STEP11-REPORT.json')
    $summary = @(
        '# 0031 Step 11 runtime capture',
        '',
        "- Mode: $($report.mode)",
        "- Captured: $($report.capturedAt)",
        "- Status: **$($report.status)**",
        "- Database data: $($report.effectiveDatabaseDataDir)",
        "- Database backing: $($report.databaseBacking)",
        "- Files selector: $($report.filesSelector)",
        "- Files backing: $($report.filesBacking)",
        "- Public Files route: $($report.publicFilesContext)/...",
        "- Responder log captured: $($report.responderLogCaptured)",
        '',
        '## Checks',
        ''
    )
    foreach ($check in $report.checks) { $summary += "- PASS - $check" }
    if ($report.error) { $summary += ''; $summary += '## Error'; $summary += ''; $summary += $report.error }
    $summary -join [Environment]::NewLine | Set-Content -LiteralPath (Join-Path $EvidenceDir 'STEP11-REPORT.md') -Encoding UTF8
    if ($transcriptStarted) {
        try { Stop-Transcript | Out-Null } catch { }
    }
}

if ($report.status -eq 'PASS') { exit 0 }
exit 1
