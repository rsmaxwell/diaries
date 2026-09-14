#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ResponderJar,
    [Parameter(Mandatory)][string]$OutputDirectory
)
# Freeze the exact Phase 10-tested artifact. This script never contacts production.
$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$change = Join-Path $repository 'change-control/in-progress/0024-FEAT - introduce reusable persistent Image catalogue'
$phase10 = Join-Path $change 'evidence/phase-10-smoke/run'
$result = Get-Content -LiteralPath (Join-Path $phase10 'summary.json') -Raw | ConvertFrom-Json
if ($result.status -ne 'PASSED' -or $result.cleanupFailures.Count) { throw 'Phase 10 must have passed and cleaned up its fixtures.' }
$tested = Get-Content -LiteralPath (Join-Path $phase10 'artifacts.json') -Raw | ConvertFrom-Json
$jar = (Get-Item -LiteralPath $ResponderJar).FullName
$jarHash = (Get-FileHash -LiteralPath $jar -Algorithm SHA256).Hash.ToLowerInvariant()
if ($jarHash -ne $tested.responder.sha256) { throw 'Responder JAR is not the exact Phase 10-tested artifact. Revalidate any replacement artifact.' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'OutputDirectory must be new.' }
$output = (New-Item -ItemType Directory -Path $OutputDirectory).FullName
$sqlDirectory = (New-Item -ItemType Directory -Path (Join-Path $output 'migration')).FullName
$phase9Sources = Get-Content -LiteralPath (Join-Path $change 'evidence/phase-09-validation/source-sha256.json') -Raw | ConvertFrom-Json
$inputs = @()
function Copy-ValidatedInput {
    param([string]$Source,[string]$Destination)
    $relative = [IO.Path]::GetRelativePath($repository,$Source).Replace('\','/')
    $expected = @($phase9Sources | Where-Object { $_.path -eq $relative })
    $hash = (Get-FileHash -LiteralPath $Source).Hash.ToLowerInvariant()
    if ($expected.Count -ne 1 -or $expected[0].sha256 -ne $hash) { throw "Input differs from Phase 9 validated source: $relative" }
    Copy-Item -LiteralPath $Source -Destination $Destination
}
Copy-Item -LiteralPath $jar -Destination (Join-Path $output 'diaries-responder.jar')
foreach ($sql in Get-ChildItem -LiteralPath (Join-Path $change 'migration') -Filter '*.sql' -File) {
    Copy-ValidatedInput $sql.FullName (Join-Path $sqlDirectory $sql.Name)
}
Copy-ValidatedInput (Join-Path $repository 'config/mosquitto/aclfile.txt') (Join-Path $output 'aclfile.txt')
$candidates = Join-Path $change 'evidence/phase-01-baseline/0022-frozen-20260912-complete/planner/image-candidates.csv'
$candidateHash = (Get-FileHash -LiteralPath $candidates).Hash.ToLowerInvariant()
if ($candidateHash -ne 'c8b0dcd5b531e133121f55e688f61afcf8d26737d1df39292505dbc01e1fe58a') { throw 'Frozen 0022 candidate inventory identity changed.' }
Copy-Item -LiteralPath $candidates -Destination (Join-Path $output '0022-image-candidates.csv')
$manifest = [ordered]@{
    change = '0024'; phase = 11; status = 'PREPARED_NOT_DEPLOYED'; createdAtUtc = [DateTime]::UtcNow.ToString('o')
    responderSha256 = $jarHash; reconciliationTool = 'com.rsmaxwell.diaries.responder.migration.migration0024.Migration0024ImageCatalogue'
    phase10SummarySha256 = (Get-FileHash -LiteralPath (Join-Path $phase10 'summary.json')).Hash.ToLowerInvariant()
    phase10ArtifactsSha256 = (Get-FileHash -LiteralPath (Join-Path $phase10 'artifacts.json')).Hash.ToLowerInvariant()
    candidateSha256 = $candidateHash
    deploymentPrerequisites = @('Confirmed target and writer-free window','One active catalogue authority per shared Files tree','Fresh database and Files backups','Startup normalization disabled','Actual NAS storage-capability verification','Schema preflight/apply/postflight in one psql session','Fresh live dry-run plan after schema creation; never reuse a clone plan','Reviewed conflict dispositions','Frozen deployment image containing this exact JAR')
}
[IO.File]::WriteAllText((Join-Path $output 'manifest.json'),($manifest | ConvertTo-Json -Depth 5))
$hashes = @(Get-ChildItem -LiteralPath $output -Recurse -File | Sort-Object FullName | ForEach-Object {
    (Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()+'  '+[IO.Path]::GetRelativePath($output,$_.FullName).Replace('\','/')
})
[IO.File]::WriteAllLines((Join-Path $output 'SHA256SUMS.txt'),$hashes)
Write-Output "Prepared $output. Production deployment has not been performed."
