#Requires -Version 7.0
<#
Read-only Step 4 publication source preflight; no Git mutation, Jenkins call,
Docker build, image push, or production action. Logs revisions and status.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$feature = Join-Path $repo 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$runId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$dir = Join-Path $feature "evidence/Step 4/private/jenkins-preflight-$runId"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$lines = [System.Collections.Generic.List[string]]::new()
function Record([string]$label,[string]$path) {
    $lines.Add("=== $label ===")
    if (!(Test-Path -LiteralPath $path)) { $lines.Add("MISSING: $path"); return }
    foreach ($cmdText in @('rev-parse --show-toplevel','branch --show-current','rev-parse HEAD','status --short')) {
        $argsList=$cmdText.Split(' ')
        $result = & git -C $path @argsList 2>&1
        $lines.Add(('git {0}' -f ($argsList -join ' ')))
        $lines.Add(($result | Out-String).TrimEnd())
        if ($LASTEXITCODE -ne 0) { $lines.Add("FAIL: Git command returned $LASTEXITCODE") }
    }
}
Record 'parent' $repo
foreach ($part in @('diaries-responder','diaries-client','diaries-web')) { Record $part (Join-Path $repo $part) }
$lines.Add('=== pinned submodules ===')
$lines.Add(((& git -C $repo submodule status) | Out-String).TrimEnd())
$lines.Add('=== configured remotes (names only; inspect URLs privately with git remote -v) ===')
$lines.Add(((& git -C $repo remote) | Out-String).TrimEnd())
$pipelineRoot = Split-Path -Parent $repo
foreach ($part in @('diaries-client-pipeline','diaries-responder-pipeline','diaries-web-pipeline')) {
    $pipeline = Join-Path $pipelineRoot "$part/Jenkinsfile"
    $lines.Add("=== $part checkout ===")
    if (Test-Path -LiteralPath $pipeline) {
        $lines.Add("Path: $pipeline")
        $checkoutLines = @(Select-String -LiteralPath $pipeline -Pattern 'branches:|userRemoteConfigs:|trackingSubmodules:|recursiveSubmodules:' | ForEach-Object { $_.Line.Trim() })
        foreach ($line in $checkoutLines) { $lines.Add($line) }
    } else { $lines.Add("NOT PRESENT: $pipeline (verify actual Jenkins job configuration)") }
}
$report = Join-Path $dir 'jenkins-source-preflight.txt'
[IO.File]::WriteAllLines($report,$lines)
Write-Host '0051 Jenkins publication preflight (read-only):'
$lines | ForEach-Object { Write-Host $_ }
Write-Host "Evidence: $report"
Write-Host 'ACTION: Verify Jenkins checkout origin/branch; commit application submodule revisions, push them, and then commit/push the parent pinned revisions before starting Jenkins. This script does not do those actions.'
