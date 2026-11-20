#Requires -Version 7.0
<# 0051 Step 3 isolated Angular editor acceptance, no production/development data mounts. #>
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$BackupFile,
  [string]$ChromeBin
)
$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$feature = Join-Path $repository 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$client = Join-Path $repository 'diaries-client'
if (!(Test-Path -LiteralPath (Join-Path $client 'node_modules/@angular/cli'))) { throw 'Angular client node_modules missing; restore its existing dependencies first.' }
$backup = (Get-Item -LiteralPath $BackupFile -ErrorAction Stop).FullName
$oldMode = $env:STEP3_EDITOR_ONLY
$oldNodePath = $env:NODE_PATH
$deps = Join-Path $env:LOCALAPPDATA 'Diaries/0051-browser-smoke/node_modules'
if (!(Test-Path -LiteralPath (Join-Path $deps 'playwright'))) { throw 'Isolated Playwright missing; use the previously installed 0051-browser-smoke dependencies.' }
$env:NODE_PATH = $deps
$evidenceRoot = Join-Path $feature 'evidence/Step 3/private'
New-Item -ItemType Directory -Force -Path $evidenceRoot | Out-Null
$runId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$buildLog = Join-Path $evidenceRoot "angular-editor-candidate-build-$runId.log"
$gitLog = Join-Path $evidenceRoot "angular-editor-source-revisions-$runId.txt"
$passed = $false
try {
  $env:STEP3_EDITOR_ONLY = '1'
  $repoStatus = & git -C $repository status --short
  $submodules = & git -C $repository submodule status
  @("Repository: $repository", "Captured UTC: $([DateTime]::UtcNow.ToString('o'))", 'Parent:',
    (& git -C $repository rev-parse HEAD), 'Parent worktree:', $repoStatus,
    'Submodules:', $submodules, 'Responder worktree:',(& git -C (Join-Path $repository 'diaries-responder') status --short),
    'Client worktree:', (& git -C $client status --short),
    'Web worktree:', (& git -C (Join-Path $repository 'diaries-web') status --short)) |
    Set-Content -LiteralPath $gitLog
  Write-Host '=== Build Angular development candidate (no deployment) ==='
  # A standalone editor origin uses a development build with base href '/',
  # not the '/diaries/' production base. No package installation or changes.
  Push-Location $client
  try {
    & npm.cmd run build -- --configuration=development *> $buildLog
    if ($LASTEXITCODE -ne 0) { throw "Angular candidate build failed; see $buildLog" }
  } finally { Pop-Location }
  Write-Host "PASS: Angular development build; log: $buildLog"
  Write-Host '=== Run editor-only disposable PostgreSQL/MQTT/Angular browser checks ==='
  $runner = Join-Path $feature 'tools/verify-step3-isolated-ui.ps1'
  $args = @{ BackupFile=$backup }
  if ($ChromeBin) { $args.ChromeBin=$ChromeBin }
  & $runner @args
  if ($LASTEXITCODE -ne 0) { throw 'Angular editor acceptance failed; inspect the integrated-* evidence directory printed above.' }
  $passed = $true
  Write-Host 'PASS: 0051 Step 3 Angular editor acceptance runner'
} finally {
  $env:STEP3_EDITOR_ONLY = $oldMode
  $env:NODE_PATH = $oldNodePath
  Write-Host "Editor build evidence: $buildLog"
  Write-Host "Source revision evidence: $gitLog"
}
if (!$passed) { exit 1 }
