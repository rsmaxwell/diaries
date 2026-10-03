[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('upload','observe','delete','cleanup')]
    [string]$Action,

    [string]$RunDirectory = '',
    [string]$ApplicationUsername = '',
    [long]$ImageId = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) { throw "0031 Step 13: $Message" }

function Read-EnvFile([string]$Path, [hashtable]$Values) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { Fail "Environment file not found: $Path" }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        if ($trimmed -notmatch '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { continue }
        $key = $matches[1]
        $value = $matches[2].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            if ($value.Length -ge 2) { $value = $value.Substring(1, $value.Length - 2) }
        }
        $Values[$key] = $value
    }
}

function Invoke-Checked([string]$Program, [object[]]$Arguments) {
    $output = & $Program @Arguments 2>&1
    $rc = $LASTEXITCODE
    if ($rc -ne 0) { Fail "$Program failed with exit code $rc`n$($output -join [Environment]::NewLine)" }
    return @($output | ForEach-Object { [string]$_ })
}

function Get-RunningContainers {
    return @(Invoke-Checked 'docker' @('ps','--format','{{.Names}}'))
}

function Get-ActiveMode {
    $running = Get-RunningContainers
    $mapping = [ordered]@{
        'diaries-development-db' = [pscustomobject]@{ Name='development-infrastructure'; Db='diaries-development-db'; Mqtt='diaries-development-mqtt'; Responder='' }
        'diaries-local-db' = [pscustomobject]@{ Name='local-docker-build'; Db='diaries-local-db'; Mqtt='diaries-local-mqtt'; Responder='diaries-local-responder' }
        'diaries-published-smoke-db' = [pscustomobject]@{ Name='local-published-smoke'; Db='diaries-published-smoke-db'; Mqtt='diaries-published-smoke-mqtt'; Responder='diaries-published-smoke-responder' }
    }
    $active = @($mapping.Keys | Where-Object { $running -contains $_ })
    if ($active.Count -ne 1) {
        Fail "Exactly one local Diaries database mode must be running; found $($active.Count): $($active -join ', ')"
    }
    $mode = $mapping[$active[0]]
    if ($running -notcontains $mode.Mqtt) { Fail "Expected MQTT container '$($mode.Mqtt)' is not running" }
    if ($mode.Responder -and $running -notcontains $mode.Responder) { Fail "Expected responder container '$($mode.Responder)' is not running" }
    return $mode
}

function Get-EffectivePair([string]$ModeName) {
    $values = @{}
    Read-EnvFile (Join-Path $ProjectRoot "config\environments\$ModeName.env") $values
    Read-EnvFile (Join-Path $ProjectRoot 'config\environments\local.env') $values
    $db = [string]$values['DIARIES_DB_DATA_DIR']
    $files = [string]$values['DIARIES_FILES_DIR']
    if ($db -ne './data/database/common' -or $files -ne 'files-development-common') {
        Fail "Step 13 requires the approved common local pair; found '$db' + '$files' for $ModeName"
    }
    return [pscustomobject]@{ Database=$db; Files=$files }
}

function Get-DatabaseIdentity([string]$Container) {
    $user = (Invoke-Checked 'docker' @('exec',$Container,'printenv','POSTGRES_USER') | Select-Object -First 1).Trim()
    $database = (Invoke-Checked 'docker' @('exec',$Container,'printenv','POSTGRES_DB') | Select-Object -First 1).Trim()
    if (-not $user -or -not $database) { Fail "Could not resolve PostgreSQL identity from $Container" }
    return [pscustomobject]@{ User=$user; Database=$database }
}

function Get-ImageRows([string]$Container, [string]$RelativePath) {
    $identity = Get-DatabaseIdentity $Container
    $quoted = $RelativePath.Replace("'", "''")
    $sql = "SELECT id,version,relative_path,mime_type,original_filename,width,height,checksum,caption,alt_text FROM image WHERE relative_path='$quoted' ORDER BY id;"
    return @(Invoke-Checked 'docker' @('exec',$Container,'psql','-X','-U',$identity.User,'-d',$identity.Database,'-At','-F',"`t",'-c',$sql) | Where-Object { $_ -ne '' })
}


function Get-ImageIdentityById([string]$Container, [long]$Id, [switch]$AllowMissing) {
    $identity = Get-DatabaseIdentity $Container
    $sql = "SELECT id,relative_path FROM image WHERE id=$Id;"
    $rows = @(Invoke-Checked 'docker' @('exec',$Container,'psql','-X','-U',$identity.User,'-d',$identity.Database,'-At','-F',"`t",'-c',$sql) | Where-Object { $_ -ne '' })
    if ($rows.Count -eq 0 -and $AllowMissing) { return $null }
    if ($rows.Count -ne 1) { Fail "Expected exactly one Image row for recovery id $Id; found $($rows.Count)" }
    $parts = @(([string]$rows[0]) -split "`t", 2)
    if ($parts.Count -ne 2) { Fail "Could not parse Image identity for recovery id $Id" }
    $relativePath = [string]$parts[1]
    if ($relativePath -notmatch '^0031-step13/0031-step13-[0-9]{8}-[0-9]{6}-[0-9a-f]{8}\.png$') {
        Fail "Recovery cleanup refuses non-Step-13 Image path '$relativePath'"
    }
    $slash = $relativePath.LastIndexOf('/')
    return [pscustomobject]@{
        Id = [long]$parts[0]
        RelativePath = $relativePath
        Subdir = $relativePath.Substring(0, $slash)
        Name = $relativePath.Substring($slash + 1)
    }
}

function Test-HttpReady {
    $uri = 'http://127.0.0.1:8081/diaries'
    $status = $null
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Method Get -Uri $uri -TimeoutSec 5
        $status = [int]$response.StatusCode
    } catch {
        # The responder static /diaries context intentionally returns 404 when
        # the context itself is requested. Windows PowerShell turns that valid
        # HTTP response into a terminating WebException, so recover its status.
        $errorResponse = $_.Exception.Response
        if ($null -eq $errorResponse) {
            Fail "Responder HTTP endpoint is not reachable at $uri : $($_.Exception.Message)"
        }
        $status = [int]$errorResponse.StatusCode
    }
    if ($status -ne 404) {
        Fail "Responder HTTP readiness expected HTTP 404 from the registered /diaries context; received HTTP $status"
    }
}

function Test-ContainerFilesPermissions([pscustomobject]$Mode) {
    if (-not $Mode.Responder) { return }

    # Avoid sh -c here. Windows PowerShell 5.1 native-command quoting can
    # split/truncate an inline shell program before Docker passes it to /bin/sh.
    # Query each path directly with stat so there are no nested shell quotes or
    # shell-local variables to preserve across PowerShell -> docker -> sh.
    $rootProbe = & docker exec $Mode.Responder stat -c '%a' /data/files 2>&1
    $rootRc = $LASTEXITCODE
    if ($rootRc -ne 0) { Fail "Could not inspect container Files permissions in $($Mode.Responder): $($rootProbe -join ' ')" }
    $rootMode = ([string]($rootProbe | Select-Object -First 1)).Trim()
    if ($rootMode -ne '700') {
        Fail "Container Files CIFS permissions are not owner-only at /data/files; expected mode 700 but found $rootMode. Recreate the mode-specific nas-photo Docker volume after applying the Step 13 compose fix."
    }

    $null = & docker exec $Mode.Responder test -d /data/files/.image-staging 2>&1
    $stagingExists = ($LASTEXITCODE -eq 0)
    if ($stagingExists) {
        $stagingProbe = & docker exec $Mode.Responder stat -c '%a' /data/files/.image-staging 2>&1
        $stagingRc = $LASTEXITCODE
        if ($stagingRc -ne 0) { Fail "Could not inspect .image-staging permissions in $($Mode.Responder): $($stagingProbe -join ' ')" }
        $stagingMode = ([string]($stagingProbe | Select-Object -First 1)).Trim()
        if ($stagingMode -ne '700') {
            Fail "Container Files CIFS permissions are not owner-only at /data/files/.image-staging; expected mode 700 but found $stagingMode. Recreate the mode-specific nas-photo Docker volume after applying the Step 13 compose fix."
        }
    }
}

function Get-DirectFilesRoot {
    $prepare = Join-Path $ProjectRoot 'scripts\windows\development-infrastructure\prepare-responder-config.bat'
    $null = Invoke-Checked $prepare @()
    $configPath = Join-Path $ProjectRoot 'build\development-infrastructure\responder.effective.json'
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if ([string]$config.diaries.files -ne 'files-development-common') { Fail 'Generated direct responder config is not using files-development-common' }
    return [System.IO.Path]::GetFullPath((Join-Path ([string]$config.diaries.root) ([string]$config.diaries.files)))
}

function Get-PhysicalFileProbe([pscustomobject]$Mode, [string]$RelativePath, [bool]$ExpectedPresent) {
    if ($Mode.Name -eq 'development-infrastructure') {
        $root = Get-DirectFilesRoot
        $path = Join-Path $root ($RelativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
        $present = Test-Path -LiteralPath $path -PathType Leaf
        $hash = if ($present) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
        if ($present -ne $ExpectedPresent) { Fail "Direct Files probe presence mismatch for $path" }
        return [pscustomobject]@{ mode='windows'; root=$root; path=$path; present=$present; sha256=$hash }
    }
    $containerPath = '/data/files/' + $RelativePath
    $probe = & docker exec $Mode.Responder sh -c "if [ -f '$containerPath' ]; then sha256sum '$containerPath'; else exit 44; fi" 2>&1
    $rc = $LASTEXITCODE
    $present = $rc -eq 0
    if ($rc -ne 0 -and $rc -ne 44) { Fail "Container Files probe failed with exit code ${rc}: $($probe -join ' ')" }
    if ($present -ne $ExpectedPresent) { Fail "Container Files probe presence mismatch for $containerPath" }
    $hash = if ($present) { ([string]($probe | Select-Object -First 1)).Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)[0].ToLowerInvariant() } else { $null }
    return [pscustomobject]@{ mode='container'; container=$Mode.Responder; path=$containerPath; present=$present; sha256=$hash }
}

function Get-Step13PhysicalCandidates([pscustomobject]$Mode) {
    if ($Mode.Name -eq 'development-infrastructure') {
        $root = Get-DirectFilesRoot
        $dir = Join-Path $root '0031-step13'
        if (-not (Test-Path -LiteralPath $dir -PathType Container)) { return @() }
        return @(Get-ChildItem -LiteralPath $dir -Filter '0031-step13-*.png' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    }
    $output = & docker exec $Mode.Responder sh -c "find /data/files/0031-step13 -maxdepth 1 -type f -name '0031-step13-*.png' -print 2>/dev/null || true" 2>&1
    if ($LASTEXITCODE -ne 0) { Fail "Could not inspect Step 13 physical candidates in $($Mode.Responder): $($output -join ' ')" }
    return @($output | ForEach-Object { [string]$_ } | Where-Object { $_ -ne '' })
}

function Write-Json([object]$Value, [string]$Path) {
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 30) + [Environment]::NewLine), $utf8)
}

function Get-ObserverCredentials([pscustomobject]$Mode) {
    $configPath = $null
    if ($Mode.Name -eq 'development-infrastructure') {
        $prepare = Join-Path $ProjectRoot 'scripts\windows\development-infrastructure\prepare-responder-config.bat'
        $null = Invoke-Checked $prepare @()
        $configPath = Join-Path $ProjectRoot 'build\development-infrastructure\responder.effective.json'
    } else {
        $values = @{}
        Read-EnvFile (Join-Path $ProjectRoot "config\environments\$($Mode.Name).env") $values
        Read-EnvFile (Join-Path $ProjectRoot 'config\environments\local.env') $values
        $raw = [string]$values['DIARIES_RESPONDER_DOCKER_CONFIG_FILE']
        if (-not $raw) { Fail "DIARIES_RESPONDER_DOCKER_CONFIG_FILE is not configured for $($Mode.Name)" }
        $expanded = [Environment]::ExpandEnvironmentVariables($raw)
        if ([System.IO.Path]::IsPathRooted($expanded)) { $configPath = $expanded }
        else { $configPath = Join-Path $ProjectRoot $expanded }
    }
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        Fail "Responder configuration for retained-state observation not found: $configPath"
    }
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $username = [string]$config.mqtt.user.username
    $password = [string]$config.mqtt.user.password
    if (-not $username -or -not $password) { Fail 'Responder MQTT observer credentials are missing from the selected responder configuration' }
    return [pscustomobject]@{ Username=$username; Password=$password; ConfigPath=$configPath }
}

function Invoke-RpcHelper([string]$Command, [string[]]$Arguments, [bool]$NeedsApplicationLogin, [pscustomobject]$Mode) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) { Fail 'Node.js was not found on PATH' }
    $mqttPackage = Join-Path $ProjectRoot 'diaries-client\node_modules\mqtt'
    if (-not (Test-Path -LiteralPath $mqttPackage -PathType Container)) {
        Fail 'diaries-client/node_modules/mqtt is missing; run npm install in diaries-client before Step 13'
    }
    $savedUser = $env:DIARIES_STEP13_APP_USERNAME
    $savedPassword = $env:DIARIES_STEP13_APP_PASSWORD
    $savedObserverUser = $env:DIARIES_STEP13_OBSERVER_USERNAME
    $savedObserverPassword = $env:DIARIES_STEP13_OBSERVER_PASSWORD
    $observer = Get-ObserverCredentials $Mode
    $env:DIARIES_STEP13_OBSERVER_USERNAME = $observer.Username
    $env:DIARIES_STEP13_OBSERVER_PASSWORD = $observer.Password
    $plain = $null
    try {
        if ($NeedsApplicationLogin) {
            if (-not $ApplicationUsername) { $script:ApplicationUsername = Read-Host 'Diaries application username (EDITOR or ADMIN)' }
            $secure = Read-Host 'Diaries application password' -AsSecureString
            $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
            $env:DIARIES_STEP13_APP_USERNAME = $ApplicationUsername
            $env:DIARIES_STEP13_APP_PASSWORD = $plain
        }
        $helper = Join-Path $ScriptDir 'step13-rpc.cjs'
        $output = Invoke-Checked $node.Source (@($helper,$Command) + $Arguments)
        return ($output -join [Environment]::NewLine) | ConvertFrom-Json
    } finally {
        $env:DIARIES_STEP13_APP_USERNAME = $savedUser
        $env:DIARIES_STEP13_APP_PASSWORD = $savedPassword
        $env:DIARIES_STEP13_OBSERVER_USERNAME = $savedObserverUser
        $env:DIARIES_STEP13_OBSERVER_PASSWORD = $savedObserverPassword
        $plain = $null
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $ScriptDir '..\..\..')).Path
$FeatureDir = Join-Path $ProjectRoot 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment'
$RuntimeRoot = Join-Path $FeatureDir 'evidence\Step 13\runtime'
$mode = Get-ActiveMode
$pair = Get-EffectivePair $mode.Name
Test-HttpReady
Test-ContainerFilesPermissions $mode

if ($Action -eq 'cleanup') {
    if ($ImageId -le 0) { Fail '-ImageId is required for cleanup' }
    if ($RunDirectory) { Fail 'Do not supply -RunDirectory for cleanup' }
    $image = Get-ImageIdentityById $mode.Db $ImageId -AllowMissing
    if ($null -eq $image) {
        $retainedCheck = Invoke-RpcHelper 'retained-check' @([string]$ImageId) $false $mode
        if ([int]$retainedCheck.nonEmptyCount -ne 0) {
            Fail "Image $ImageId is absent from the database but retained Image state still exists"
        }
        $candidates = @(Get-Step13PhysicalCandidates $mode)
        if ($candidates.Count -ne 0) {
            Fail "Image $ImageId is absent from the database, but Step 13 physical candidate file(s) remain and cannot be mapped safely: $($candidates -join ', ')"
        }
        $recoveryDir = Join-Path $RuntimeRoot 'recovery'
        New-Item -ItemType Directory -Force -Path $recoveryDir | Out-Null
        $proofPath = Join-Path $recoveryDir "CLEANUP-IMAGE-$ImageId.json"
        Write-Json ([ordered]@{ capturedAt=(Get-Date).ToUniversalTime().ToString('o'); mode=$mode.Name; pair=$pair; imageId=$ImageId; alreadyAbsent=$true; retainedCheck=$retainedCheck; step13PhysicalCandidates=$candidates }) $proofPath
        Write-Host "PASS: Step 13 Image $ImageId is already absent; retained state and Step 13 physical candidates are also absent."
        Write-Host "Evidence: $proofPath"
        exit 0
    }
    $beforeFile = Get-PhysicalFileProbe $mode $image.RelativePath $true
    $rpc = Invoke-RpcHelper 'cleanup' @($image.Name,$image.Subdir,[string]$image.Id) $true $mode
    $remaining = @(Get-ImageRows $mode.Db $image.RelativePath)
    if ($remaining.Count -ne 0) { Fail "Recovery cleanup left $($remaining.Count) Image row(s) for $($image.RelativePath)" }
    $afterFile = Get-PhysicalFileProbe $mode $image.RelativePath $false
    $recoveryDir = Join-Path $RuntimeRoot 'recovery'
    New-Item -ItemType Directory -Force -Path $recoveryDir | Out-Null
    $proofPath = Join-Path $recoveryDir "CLEANUP-IMAGE-$ImageId.json"
    Write-Json ([ordered]@{ capturedAt=(Get-Date).ToUniversalTime().ToString('o'); mode=$mode.Name; pair=$pair; image=$image; physicalFileBefore=$beforeFile; cleanupRpc=$rpc; physicalFileAfter=$afterFile }) $proofPath
    Write-Host "PASS: safely removed unrecorded Step 13 Image $ImageId using deleteImage."
    Write-Host "Evidence: $proofPath"
    exit 0
}

if ($Action -eq 'upload') {
    if ($RunDirectory) { Fail 'Do not supply -RunDirectory for upload; a unique runtime directory is created automatically' }
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $token = [guid]::NewGuid().ToString('N').Substring(0,8)
    $name = "0031-step13-$timestamp-$token.png"
    $subdir = '0031-step13'
    New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
    $RunDirectory = Join-Path $RuntimeRoot "local-$timestamp-$token"
    New-Item -ItemType Directory -Path $RunDirectory | Out-Null
    $rpc = Invoke-RpcHelper 'upload' @($name,$subdir) $true $mode
    $relativePath = [string]$rpc.fixture.relativePath
    $rows = @(Get-ImageRows $mode.Db $relativePath)
    if ($rows.Count -ne 1) { Fail "Expected exactly one local Image row after upload; found $($rows.Count)" }
    $file = Get-PhysicalFileProbe $mode $relativePath $true
    if ($file.sha256 -ne [string]$rpc.fixture.sha256) { Fail 'Physical local file checksum does not match the uploaded fixture' }
    $state = [ordered]@{
        schemaVersion = 1
        feature = '0031-FEAT'
        step = 13
        capturedAt = (Get-Date).ToUniversalTime().ToString('o')
        uploadMode = $mode.Name
        effectiveDbDataDir = $pair.Database
        effectiveFilesDir = $pair.Files
        imageId = [int64]$rpc.imageId
        name = $name
        subdir = $subdir
        relativePath = $relativePath
        publicUrl = [string]$rpc.uploadReply.payload.url
        sha256 = [string]$rpc.fixture.sha256
        size = [int64]$rpc.fixture.size
    }
    Write-Json $state (Join-Path $RunDirectory 'STATE.json')
    Write-Json $rpc (Join-Path $RunDirectory 'UPLOAD-RPC.json')
    Write-Json ([ordered]@{ mode=$mode.Name; pair=$pair; databaseRows=$rows; physicalFile=$file }) (Join-Path $RunDirectory 'UPLOAD-LOCAL-PROOF.json')
    Write-Host "PASS: uploaded disposable Image in $($mode.Name), proved DB row, retained topic, physical file and stable /files URL."
    Write-Host "Evidence: $RunDirectory"
    Write-Host 'NEXT: stop this mode, start a different local mode using the same common pair, then run observe with this RunDirectory.'
    exit 0
}

if (-not $RunDirectory) { Fail '-RunDirectory is required for observe and delete' }
$RunDirectory = (Resolve-Path -LiteralPath $RunDirectory).Path
$statePath = Join-Path $RunDirectory 'STATE.json'
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { Fail "STATE.json not found in $RunDirectory" }
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ([string]$state.effectiveDbDataDir -ne $pair.Database -or [string]$state.effectiveFilesDir -ne $pair.Files) {
    Fail 'Current mode does not resolve the same common durable pair recorded by the upload'
}

if ($Action -eq 'observe') {
    if ($mode.Name -eq [string]$state.uploadMode) {
        Fail "Observe must run from a second local mode; upload was performed in '$($state.uploadMode)' and that same mode is active"
    }
    $rows = @(Get-ImageRows $mode.Db ([string]$state.relativePath))
    if ($rows.Count -ne 1) { Fail "Second mode did not see exactly one shared Image row; found $($rows.Count)" }
    $file = Get-PhysicalFileProbe $mode ([string]$state.relativePath) $true
    if ($file.sha256 -ne [string]$state.sha256) { Fail 'Second mode physical file checksum differs from upload fixture' }
    $rpc = Invoke-RpcHelper 'observe' @($statePath) $false $mode
    $proof = [ordered]@{ capturedAt=(Get-Date).ToUniversalTime().ToString('o'); uploadMode=$state.uploadMode; observeMode=$mode.Name; pair=$pair; databaseRows=$rows; physicalFile=$file; retainedAndHttp=$rpc }
    Write-Json $proof (Join-Path $RunDirectory "OBSERVE-$($mode.Name).json")
    Write-Host "PASS: $($mode.Name) sees the same Image row, bytes, retained Image and /files URL created by $($state.uploadMode)."
    Write-Host 'NEXT: keep this mode active (or switch to another common-pair local mode) and run delete with the same RunDirectory.'
    exit 0
}

$observations = @(Get-ChildItem -LiteralPath $RunDirectory -Filter 'OBSERVE-*.json' -File -ErrorAction SilentlyContinue)
if ($observations.Count -lt 1) { Fail 'Delete is blocked until a successful second-mode OBSERVE-*.json proof exists' }
$beforeRows = @(Get-ImageRows $mode.Db ([string]$state.relativePath))
if ($beforeRows.Count -ne 1) { Fail "Expected one Image row immediately before delete; found $($beforeRows.Count)" }
$beforeFile = Get-PhysicalFileProbe $mode ([string]$state.relativePath) $true
$rpcDelete = Invoke-RpcHelper 'delete' @($statePath) $true $mode
$afterRows = @(Get-ImageRows $mode.Db ([string]$state.relativePath))
if ($afterRows.Count -ne 0) { Fail "Image row remains after supported deleteImage operation: $($afterRows.Count) row(s)" }
$afterFile = Get-PhysicalFileProbe $mode ([string]$state.relativePath) $false
$proof = [ordered]@{
    capturedAt=(Get-Date).ToUniversalTime().ToString('o')
    deleteMode=$mode.Name
    pair=$pair
    databaseRowsBefore=$beforeRows
    physicalFileBefore=$beforeFile
    deleteRpc=$rpcDelete
    databaseRowsAfter=$afterRows
    physicalFileAfter=$afterFile
}
Write-Json $proof (Join-Path $RunDirectory 'DELETE-LOCAL-PROOF.json')
Write-Host "PASS: deleteImage removed the common-dataset row, retained topic and physical file in $($mode.Name)."
Write-Host "Evidence: $RunDirectory"
Write-Host 'NEXT: on pluto capture the Step 13 production AFTER control and compare it with the production BEFORE control.'
