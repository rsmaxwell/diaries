[CmdletBinding()]
param([Parameter(Mandatory)][string]$WorkDirectory)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $WorkDirectory) { throw 'Choose a new test directory.' }
$work = New-Item -ItemType Directory -Path $WorkDirectory
$root = New-Item -ItemType Directory -Path (Join-Path $work.FullName 'files')
$outside = New-Item -ItemType Directory -Path (Join-Path $work.FullName 'outside')
$fixtureRoot = Join-Path $PSScriptRoot '..\rpc-responses\capture-20260912\fixtures'
$png = [IO.File]::ReadAllBytes((Join-Path $fixtureRoot 'plain.png'))
$jpeg = [IO.File]::ReadAllBytes((Join-Path $fixtureRoot 'dated.jpg'))
$expected = @{}
function Add-Fixture {
    param([string]$Name, [byte[]]$Bytes, [string]$Type, [string]$Status, [string]$ExtensionStatus)
    [IO.File]::WriteAllBytes((Join-Path $root.FullName $Name), $Bytes)
    $expected[$Name] = @($Type, $Status, $ExtensionStatus)
}
Add-Fixture 'normal.png' $png 'image/png' 'IMAGE_SIGNATURE' 'MATCH'
Add-Fixture 'renamed.jpg' $png 'image/png' 'IMAGE_SIGNATURE' 'MISMATCH'
Add-Fixture 'image.bin' $png 'image/png' 'IMAGE_SIGNATURE' 'MISMATCH'
Add-Fixture 'no-extension' $jpeg 'image/jpeg' 'IMAGE_SIGNATURE' 'MISMATCH'
Add-Fixture 'normal.JPEG' $jpeg 'image/jpeg' 'IMAGE_SIGNATURE' 'MATCH'
Add-Fixture 'fake.png' ([Text.Encoding]::UTF8.GetBytes('ordinary text')) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'empty.jpg' ([byte[]]@()) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'short.png' ([byte[]]@(0x89, 0x50, 0x4e)) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'short.jpg' ([byte[]]@(0xff, 0xd8)) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'embedded-signature.bin' ([byte[]](@(0) + $png)) '' 'NO_SUPPORTED_SIGNATURE' 'NOT_APPLICABLE'
# Header-only fixtures deliberately prove candidate detection, not full decoding.
foreach ($version in @('GIF87a','GIF89a')) {
    Add-Fixture ($version + '.gif') ([Text.Encoding]::ASCII.GetBytes($version)) 'image/gif' 'IMAGE_SIGNATURE' 'MATCH'
}
foreach ($chunk in @('VP8 ', 'VP8L', 'VP8X')) {
    $bytes = [byte[]]([Text.Encoding]::ASCII.GetBytes('RIFF') + @(20,0,0,0) + [Text.Encoding]::ASCII.GetBytes('WEBP' + $chunk))
    Add-Fixture ($chunk.Trim() + '.webp') $bytes 'image/webp' 'IMAGE_SIGNATURE' 'MATCH'
}
Add-Fixture 'wave.webp' ([byte[]]([Text.Encoding]::ASCII.GetBytes('RIFF') + @(20,0,0,0) + [Text.Encoding]::ASCII.GetBytes('WAVEfmt '))) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'bad-chunk.webp' ([byte[]]([Text.Encoding]::ASCII.GetBytes('RIFF') + @(20,0,0,0) + [Text.Encoding]::ASCII.GetBytes('WEBPFAKE'))) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'short.webp' ([byte[]]([Text.Encoding]::ASCII.GetBytes('RIFF') + @(20,0,0,0) + [Text.Encoding]::ASCII.GetBytes('WEBP'))) '' 'NO_SUPPORTED_SIGNATURE' 'MISMATCH'
Add-Fixture 'locked.png' $png '' 'UNREADABLE' 'NOT_APPLICABLE'
$nested = New-Item -ItemType Directory -Path (Join-Path $root.FullName 'nested space')
[IO.File]::WriteAllBytes((Join-Path $nested.FullName 'image [1].png'), $png)
$expected['nested space/image [1].png'] = @('image/png', 'IMAGE_SIGNATURE', 'MATCH')
[IO.File]::WriteAllBytes((Join-Path $outside.FullName 'must-not-scan.png'), $png)
$null = New-Item -ItemType Junction -Path (Join-Path $root.FullName 'linked-directory') -Target $outside.FullName
$before = @{}
foreach ($name in $expected.Keys) { $before[$name] = (Get-FileHash -LiteralPath (Join-Path $root.FullName $name)).Hash }
$lock = [IO.File]::Open((Join-Path $root.FullName 'locked.png'), [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
try {
    & (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot ($root.FullName + '\') -OutputFile (Join-Path $work.FullName 'inventory.csv')
} finally { $lock.Dispose() }
$rows = @(Import-Csv -LiteralPath (Join-Path $work.FullName 'inventory.csv') -Encoding UTF8)
if ($rows.Count -ne ($expected.Count + 2)) { throw 'Unexpected entry count or followed junction.' }
foreach ($name in $expected.Keys) {
    $actual = @($rows | Where-Object relativePath -eq $name)
    if ($actual.Count -ne 1) { throw "Missing/duplicate path: $name" }
    if ($actual[0].detectedMimeType -cne $expected[$name][0] -or $actual[0].signatureStatus -cne $expected[$name][1] -or
        $actual[0].extensionStatus -cne $expected[$name][2]) { throw "Unexpected content classification: $name" }
    if ((Get-FileHash -LiteralPath (Join-Path $root.FullName $name)).Hash -cne $before[$name]) { throw "Fixture was modified: $name" }
}
$link = $rows | Where-Object relativePath -eq 'linked-directory'
if ($link.entryType -ne 'link' -or $link.signatureStatus -ne 'SKIPPED_LINK' -or $link.headerBytesRead -ne '0') { throw 'Link was not skipped.' }
if ([string]::IsNullOrWhiteSpace(($rows | Where-Object relativePath -eq 'locked.png').inspectionError)) { throw 'Unreadable file lacks explanation.' }
$empty = New-Item -ItemType Directory -Path (Join-Path $work.FullName 'empty')
& (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot $empty.FullName -OutputFile (Join-Path $work.FullName 'empty.csv')
if (@(Import-Csv -LiteralPath (Join-Path $work.FullName 'empty.csv')).Count -ne 0) { throw 'Invalid empty inventory.' }
$preserved = (Get-FileHash -LiteralPath (Join-Path $work.FullName 'inventory.csv')).Hash
$rejected = $false
try { & (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot $root.FullName -OutputFile (Join-Path $work.FullName 'inventory.csv') }
catch { $rejected = $true }
if (!$rejected -or (Get-FileHash -LiteralPath (Join-Path $work.FullName 'inventory.csv')).Hash -cne $preserved) { throw 'Existing evidence was not preserved.' }
$summary = Get-Content -Raw -LiteralPath (Join-Path $work.FullName 'inventory.summary.json') | ConvertFrom-Json
if ($summary.totals.entries -ne 22 -or $summary.totals.regularFiles -ne 20 -or
    $summary.totals.directoriesExcludingRoot -ne 1 -or $summary.totals.symlinksOrReparsePoints -ne 1 -or
    $summary.totals.imageCandidates -ne 11 -or $summary.totals.unreadableHeaders -ne 1 -or
    $summary.totals.filesWithoutSupportedImageSignature -ne 8 -or $summary.totals.extensionMismatches -ne 10) { throw 'Summary counts do not match the test dataset.' }
if ($summary.source.inventorySha256 -cne $preserved.ToLowerInvariant()) { throw 'Summary is not tied to its CSV hash.' }
if ($summary.headerInspection.fullFileReadabilityChecked -or $null -ne $summary.headerInspection.fullFileUnreadableCount -or
    $summary.caseFoldedPathCollisions.checked -or $null -ne $summary.caseFoldedPathCollisions.groupCount) { throw 'Summary claims unperformed checks.' }
$emptySummary = Get-Content -Raw -LiteralPath (Join-Path $work.FullName 'empty.summary.json') | ConvertFrom-Json
if ($emptySummary.totals.entries -ne 0 -or $emptySummary.imageCandidatesByDetectedMimeType.'image/png' -ne 0 -or
    @($emptySummary.unreadableHeaders).Count -ne 0) { throw 'Empty summary must have explicit zero counts and empty arrays.' }
$placeholder = Join-Path $work.FullName 'placeholder.json'
[IO.File]::WriteAllText($placeholder, '')
& (Join-Path $PSScriptRoot 'summarize-files-root-inventory.ps1') -InventoryFile (Join-Path $work.FullName 'inventory.csv') -SummaryFile $placeholder -ReplaceEmptyOutput
$summaryHash = (Get-FileHash -LiteralPath $placeholder).Hash
$rejected = $false
try { & (Join-Path $PSScriptRoot 'summarize-files-root-inventory.ps1') -InventoryFile (Join-Path $work.FullName 'inventory.csv') -SummaryFile $placeholder -ReplaceEmptyOutput }
catch { $rejected = $true }
if (!$rejected -or (Get-FileHash -LiteralPath $placeholder).Hash -cne $summaryHash) { throw 'Nonempty summary was not preserved.' }
Write-Output "PASS: PowerShell $($PSVersionTable.PSVersion); $($expected.Count) file cases; junction skipped; empty root; no blank paths; input bytes and existing report preserved."
Write-Output 'PASS: summary counts, source hash, unchecked-state markers, empty summaries and protected placeholder replacement.'
