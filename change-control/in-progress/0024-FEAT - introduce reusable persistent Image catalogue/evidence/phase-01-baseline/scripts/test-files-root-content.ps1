[CmdletBinding()]
param([Parameter(Mandatory)][string]$WorkDirectory)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $WorkDirectory) { throw 'Choose a new test directory.' }
$work = (New-Item -ItemType Directory -Path $WorkDirectory).FullName
$root = (New-Item -ItemType Directory -Path (Join-Path $work 'files')).FullName
$outside = (New-Item -ItemType Directory -Path (Join-Path $work 'outside')).FullName
$nested = (New-Item -ItemType Directory -Path (Join-Path $root 'nested space')).FullName
$large = New-Object byte[] 150003
for ($i=0; $i -lt $large.Length; $i++) { $large[$i] = $i % 251 }
[IO.File]::WriteAllBytes((Join-Path $nested 'large [1].bin'), $large)
[IO.File]::WriteAllBytes((Join-Path $root 'empty.bin'), (New-Object byte[] 0))
[IO.File]::WriteAllText((Join-Path $root 'locked.txt'), 'fixture for lock test')
[IO.File]::WriteAllText((Join-Path $outside 'not-scanned.txt'), 'outside fixture')
$null = New-Item -ItemType Junction -Path (Join-Path $root 'linked') -Target $outside
[IO.Directory]::SetLastWriteTimeUtc($nested, [DateTime]::UtcNow.AddMinutes(-1))
$baseline = Join-Path $work 'baseline.csv'
& (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot $root -OutputFile $baseline
$output = Join-Path $work 'clean'
& (Join-Path $PSScriptRoot 'verify-files-root-content.ps1') -FilesRoot $root -BaselineInventory $baseline -OutputDirectory $output
$summary = Get-Content -Raw -LiteralPath (Join-Path $output 'verification-summary.json') | ConvertFrom-Json
if (!$summary.clean -or $summary.regularFiles -ne 3 -or $summary.skippedLinks -ne 1 -or $summary.directories -ne 1 -or $summary.fullFileReadability.readableFiles -ne 3) { throw 'Clean fixture did not reconcile.' }
$reads = @(Import-Csv -LiteralPath (Join-Path $output 'file-readability.csv'))
foreach ($row in $reads) {
    if ($row.sha256 -cne (Get-FileHash -LiteralPath (Join-Path $root $row.relativePath)).Hash.ToLowerInvariant() -or $row.bytesRead -ne $row.expectedBytes) { throw 'Full-file hash or length mismatch.' }
}
if ((Get-Item -LiteralPath (Join-Path $output 'path-conflicts.csv')).Length -eq 0 -or @(Import-Csv -LiteralPath (Join-Path $output 'path-conflicts.csv')).Count -ne 0) { throw 'Zero-conflict CSV needs a header and no rows.' }
foreach ($line in Get-Content -LiteralPath (Join-Path $output 'SHA256SUMS.txt')) {
    $parts = $line -split '  ',2
    if ($parts[0] -cne (Get-FileHash -LiteralPath (Join-Path $output $parts[1])).Hash.ToLowerInvariant()) { throw 'Manifest mismatch.' }
}
$rejected=$false
try { & (Join-Path $PSScriptRoot 'verify-files-root-content.ps1') -FilesRoot $root -BaselineInventory $baseline -OutputDirectory $output } catch { $rejected=$true }
if (!$rejected) { throw 'Existing evidence was overwritten.' }

# A held exclusive lock must become a reported failure, while an added path
# must invalidate baseline equality. Neither may produce a clean summary.
[IO.File]::WriteAllText((Join-Path $root 'new.txt'), 'new file after baseline')
$lock = [IO.File]::Open((Join-Path $root 'locked.txt'), [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
try {
    & (Join-Path $PSScriptRoot 'verify-files-root-content.ps1') -FilesRoot $root -BaselineInventory $baseline -OutputDirectory (Join-Path $work 'failures')
} finally { $lock.Dispose() }
$failed = Get-Content -Raw -LiteralPath (Join-Path $work 'failures/verification-summary.json') | ConvertFrom-Json
if ($failed.clean -or $failed.baselineUnchanged -or $failed.fullFileReadability.failedFiles -ne 1 -or $failed.fullFileReadability.readableFiles -ne 3) { throw 'Unreadable file or baseline drift was not reported.' }

# Synthetic inventories allow case-sensitive and NFC-alias tests on Windows.
$decomposed = 'caf' + 'e' + [char]0x301 + '.png'
$composed = 'caf' + [char]0xe9 + '.png'
$collisionRows = @(
    [pscustomobject]@{relativePath='A/Image.JPG'; entryType='file'},
    [pscustomobject]@{relativePath='a/image.jpg'; entryType='file'},
    [pscustomobject]@{relativePath=$composed; entryType='file'},
    [pscustomobject]@{relativePath=$decomposed; entryType='file'},
    [pscustomobject]@{relativePath='Dir'; entryType='directory'},
    [pscustomobject]@{relativePath='dir'; entryType='file'},
    [pscustomobject]@{relativePath='unique.png'; entryType='file'}
)
$conflicts = @(& (Join-Path $PSScriptRoot 'find-case-folded-path-conflicts.ps1') -Rows $collisionRows)
if ($conflicts.Count -ne 6 -or @($conflicts | Select-Object -ExpandProperty foldedPath -Unique).Count -ne 3) { throw 'Case or NFC collision was missed.' }
$rejected=$false
try { & (Join-Path $PSScriptRoot 'find-case-folded-path-conflicts.ps1') -Rows @([pscustomobject]@{relativePath='../escape'; entryType='file'}) } catch { $rejected=$true }
if (!$rejected) { throw 'Traversal path was accepted.' }
$empty = (New-Item -ItemType Directory -Path (Join-Path $work 'empty')).FullName
& (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot $empty -OutputFile (Join-Path $work 'empty.csv')
& (Join-Path $PSScriptRoot 'verify-files-root-content.ps1') -FilesRoot $empty -BaselineInventory (Join-Path $work 'empty.csv') -OutputDirectory (Join-Path $work 'empty-check')
$emptySummary = Get-Content -Raw -LiteralPath (Join-Path $work 'empty-check/verification-summary.json') | ConvertFrom-Json
if (!$emptySummary.clean -or $emptySummary.regularFiles -ne 0) { throw 'Empty-root verification failed.' }
Write-Output "PASS: PowerShell $($PSVersionTable.PSVersion); full reads across buffer boundaries, empty files/root, SHA-256, junction skip, locked-file failure, inventory drift, case/NFC/file-directory collisions, traversal rejection, overwrite prevention and manifest verification."
