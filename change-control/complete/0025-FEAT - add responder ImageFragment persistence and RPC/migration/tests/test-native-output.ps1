[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Container,
    [Parameter(Mandatory)][string]$Database,
    [Parameter(Mandatory)][string]$User,
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [string]$SchemaDirectory
)
$ErrorActionPreference = 'Stop'
$evidence = (New-Item -ItemType Directory -Path $EvidenceDirectory -ErrorAction Stop).FullName
$runner = Join-Path $PSScriptRoot '../run-migration.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $runner).Path, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Runner parsing failed' }
# Load only the capture helpers, never the migration body.
foreach ($name in @('Docker-Captured', 'Docker-Checked')) {
    $definition = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $true)
    if (!$definition) { throw "Missing $name" }
    . ([scriptblock]::Create($definition.Extent.Text))
}
$base = @('exec',$Container,'psql','-X','-U',$User,'-d',$Database,'-v','ON_ERROR_STOP=1')
$noticeSql = 'DO $$ BEGIN RAISE NOTICE ''0025 notice handling probe''; END $$;'
$failureSql = 'DO $$ BEGIN RAISE EXCEPTION ''0025 deliberate failure probe''; END $$;'
$notice = Docker-Captured ($base + @('-c',$noticeSql))
$failure = Docker-Captured ($base + @('-c',$failureSql))
$notice.Output | Out-String | Set-Content (Join-Path $evidence 'notice.log')
$failure.Output | Out-String | Set-Content (Join-Path $evidence 'deliberate-error.log')
if ($notice.ExitCode -ne 0 -or ($notice.Output -join "`n") -notmatch 'notice handling probe') { throw 'Notice capture failed' }
if ($failure.ExitCode -eq 0 -or ($failure.Output -join "`n") -notmatch 'deliberate failure probe') { throw 'Failure capture failed' }
$null = Docker-Checked ($base + @('-c',$noticeSql))
$rejected = $false
try { $null = Docker-Checked ($base + @('-c',$failureSql)) }
catch { if ($_.Exception.Message -notmatch 'deliberate failure probe') { throw }; $rejected = $true }
if (!$rejected) { throw 'Nonzero exit code was not rejected' }
if ($SchemaDirectory) {
    # Preflight/postflight create temporary validation objects only. No apply SQL.
    $verification = Docker-Captured ($base + @('-f',"$SchemaDirectory/001-preflight.sql",'-f',"$SchemaDirectory/003-postflight.sql"))
    ($verification.Output -join "`n") | Set-Content (Join-Path $evidence 'schema-verification.log')
    if ($verification.ExitCode -ne 0) { throw 'Schema verification failed' }
}
[ordered]@{
    status = 'PASSED'
    powershell = $PSVersionTable.PSVersion.ToString()
    noticeExitCode = $notice.ExitCode
    deliberateErrorExitCode = $failure.ExitCode
    checkedHelperRejectedError = $rejected
    schemaVerified = [bool]$SchemaDirectory
    applicationRowsModified = $false
    migrationApplied = $false
    runnerSha256 = (Get-FileHash $runner).Hash.ToLowerInvariant()
} | ConvertTo-Json | Tee-Object -FilePath (Join-Path $evidence 'result.json')
