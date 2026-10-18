# 0036 Gate E: Diaries-only, read-only source dependency audit.
param([string]$DiariesRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $DiariesRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) { throw "Not a Git working tree: $root" }
$terms = @('diaries_0036_', 'DIARIES_0036_', 'pre-0036-rollback', 'publish-preflight', 'fixed-capture', 'fixed-destination')
$extensions = @('.yaml','.yml','.j2','.sh','.py','.service','.env','.ps1')
$excluded = @('.git','node_modules','build','dist','change-control')
Write-Output '0036 Gate E Diaries source audit (read-only)'
Write-Output "Root: $root"
Write-Output 'Git commit:'
& git -C $root rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'git rev-parse failed' }
Write-Output 'Git status:'
& git -C $root status --short
if ($LASTEXITCODE -ne 0) { throw 'git status failed' }
$files = Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object {
  $relative = $_.FullName.Substring($root.Length).TrimStart('\','/')
  $parts = $relative -split '[\/]'
  -not (@($parts | Where-Object { $_ -in $excluded }).Count) -and ($_.Extension -in $extensions -or $_.Name -like '*.env')
}
foreach ($term in $terms) {
  Write-Output "`n-- references: $term --"
  $matches = $files | Select-String -SimpleMatch -Pattern $term -List -ErrorAction Stop |
    ForEach-Object { $_.Path.Substring($root.Length).TrimStart('\','/') } | Sort-Object -Unique
  $matches | Write-Output
}
Write-Output "`nRead-only audit completed; no deployment or deletion performed."
