[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$FilesRoot,
    [Parameter(Mandatory)][string]$BaselineInventory,
    [Parameter(Mandatory)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$started = [DateTime]::UtcNow.ToString('o')
$root = Get-Item -LiteralPath $FilesRoot -Force
if (!$root.PSIsContainer -or $root.PSProvider.Name -ne 'FileSystem' -or ($root.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'FilesRoot must be a regular filesystem directory.' }
$prefix = $root.FullName.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
$output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
if ($output.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $output)) { throw 'Choose a new output directory outside the Files root.' }
$baseline = (Resolve-Path -LiteralPath $BaselineInventory).Path
$baselineHash = (Get-FileHash -LiteralPath $baseline).Hash.ToLowerInvariant()
$null = New-Item -ItemType Directory -Path $output

function Write-Evidence {
    param([string]$Name, [string]$Text)
    $stream = [IO.File]::Open((Join-Path $output $Name), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $writer = New-Object IO.StreamWriter($stream, (New-Object Text.UTF8Encoding($false)))
        try { $writer.Write($Text) } finally { $writer.Dispose() }
    } finally { $stream.Dispose() }
}
function Write-CsvEvidence {
    param([string]$Name, [object[]]$Rows, [string]$Header)
    $lines = @($Header)
    if ($Rows.Count -gt 0) { $lines = @($Rows | ConvertTo-Csv -NoTypeInformation) }
    Write-Evidence $Name (($lines -join "`r`n") + "`r`n")
}
function Assert-NoLinks {
    param([string]$RelativePath)
    $cursor = $root.FullName
    foreach ($segment in $RelativePath.Split('/')) {
        $cursor = Join-Path $cursor $segment
        $item = Get-Item -LiteralPath $cursor -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Path became a link/reparse point; refusing to follow it.' }
    }
}

# Validate and copy the frozen input before any use; retain its exact bytes.
& (Join-Path $PSScriptRoot 'summarize-files-root-inventory.ps1') -InventoryFile $baseline -SummaryFile (Join-Path $output 'baseline-header-summary.json')
[IO.File]::Copy($baseline, (Join-Path $output 'baseline-inventory.csv'), $false)
if ((Get-FileHash -LiteralPath (Join-Path $output 'baseline-inventory.csv')).Hash.ToLowerInvariant() -cne $baselineHash) { throw 'Baseline changed while being copied.' }
& (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot $root.FullName -OutputFile (Join-Path $output 'inventory-before.csv')
$rows = @(Import-Csv -LiteralPath (Join-Path $output 'inventory-before.csv') -Encoding UTF8)
$conflicts = @(& (Join-Path $PSScriptRoot 'find-case-folded-path-conflicts.ps1') -Rows $rows)
Write-CsvEvidence 'path-conflicts.csv' $conflicts '"foldedPath","relativePath","entryType","groupSize"'
$results = @(
    foreach ($row in $rows | Where-Object entryType -eq 'file') {
        $result = [ordered]@{relativePath=$row.relativePath; expectedBytes=[long]$row.Length; bytesRead=[long]0; sha256=''; status='UNREADABLE'; error=''}
        $stream = $null; $sha = $null
        try {
            Assert-NoLinks $row.relativePath
            $path = Join-Path $root.FullName $row.relativePath
            $before = Get-Item -LiteralPath $path -Force
            if ($before.Length -ne [long]$row.Length -or $before.LastWriteTimeUtc.ToString('o') -cne $row.lastModifiedUtc) { throw 'File metadata changed since inventory.' }
            $stream = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
            $sha = [Security.Cryptography.SHA256]::Create()
            $buffer = New-Object byte[] 65536
            while (($count = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
                $null = $sha.TransformBlock($buffer, 0, $count, $buffer, 0)
                $result.bytesRead += $count
            }
            $null = $sha.TransformFinalBlock((New-Object byte[] 0), 0, 0)
            $after = Get-Item -LiteralPath $path -Force
            if ($result.bytesRead -ne [long]$row.Length -or $after.Length -ne $before.Length -or $after.LastWriteTimeUtc -ne $before.LastWriteTimeUtc) { throw 'File changed during full read.' }
            $result.sha256 = [BitConverter]::ToString($sha.Hash).Replace('-','').ToLowerInvariant()
            $result.status = 'READABLE'
        } catch { $result.error = $_.Exception.GetBaseException().Message }
        finally {
            if ($stream) { $stream.Dispose() }
            if ($sha) { $sha.Dispose() }
        }
        [pscustomobject]$result
    }
)
Write-CsvEvidence 'file-readability.csv' $results '"relativePath","expectedBytes","bytesRead","sha256","status","error"'
# Re-enumerate to report additions/removals and metadata/header changes during the check.
& (Join-Path $PSScriptRoot 'generate-files-root-inventory.ps1') -FilesRoot $root.FullName -OutputFile (Join-Path $output 'inventory-after.csv')
$fields = @('relativePath','entryType','Length','Extension','lastModifiedUtc','LinkType','detectedMimeType','signatureStatus','headerBytesRead','headerHex','extensionStatus')
function Compare-Inventories {
    param([string]$Left, [string]$Right)
    $a = @(Import-Csv -LiteralPath $Left -Encoding UTF8 | Select-Object $fields | ConvertTo-Csv -NoTypeInformation)
    $b = @(Import-Csv -LiteralPath $Right -Encoding UTF8 | Select-Object $fields | ConvertTo-Csv -NoTypeInformation)
    if ($a.Count -eq 0 -and $b.Count -eq 0) { return }
    if ($a.Count -eq 0) { foreach ($line in $b) { [pscustomobject]@{InputObject=$line; SideIndicator='=>'} }; return }
    if ($b.Count -eq 0) { foreach ($line in $a) { [pscustomobject]@{InputObject=$line; SideIndicator='<='} }; return }
    Compare-Object -ReferenceObject $a -DifferenceObject $b -CaseSensitive
}
$baselineChanges = @(Compare-Inventories (Join-Path $output 'baseline-inventory.csv') (Join-Path $output 'inventory-before.csv'))
$duringChanges = @(Compare-Inventories (Join-Path $output 'inventory-before.csv') (Join-Path $output 'inventory-after.csv'))
Write-Evidence 'inventory-comparison.json' (([ordered]@{comparedFields=$fields; baselineToBefore=$baselineChanges; beforeToAfter=$duringChanges; note='<= means earlier row; => means later row. Error message wording is excluded.'} | ConvertTo-Json -Depth 6) + "`n")
$failed = @($results | Where-Object status -ne 'READABLE')
$groupCount = @($conflicts | Select-Object -ExpandProperty foldedPath -Unique).Count
$nonAscii = @($rows | Where-Object relativePath -match '[^\x00-\x7F]').Count
$summary = [ordered]@{
    schemaVersion=1; startedAtUtc=$started; completedAtUtc=[DateTime]::UtcNow.ToString('o'); filesRoot=$root.FullName; powershellVersion=$PSVersionTable.PSVersion.ToString()
    baselineInventoryFile=[IO.Path]::GetFileName($baseline); baselineInventorySha256=$baselineHash
    entries=$rows.Count; regularFiles=$results.Count; directories=@($rows | Where-Object entryType -eq 'directory').Count; skippedLinks=@($rows | Where-Object entryType -eq 'link').Count
    fullFileReadability=[ordered]@{checked=$true; readableFiles=$results.Count-$failed.Count; failedFiles=$failed.Count; bytesRead=($results | Measure-Object bytesRead -Sum).Sum; report='file-readability.csv'; method='Read-only streams through EOF, SHA-256 over all bytes, expected length and modification-time checks; reparse points skipped.'}
    caseFoldedPathCollisions=[ordered]@{checked=$true; entriesChecked=$rows.Count; groupCount=$groupCount; conflictingEntries=$conflicts.Count; nonAsciiPaths=$nonAscii; report='path-conflicts.csv'; rule='Slash separators, NFC normalization, invariant lowercase, ordinal comparison across files, directories and links.'; note='Invariant lowercase is the explicit baseline rule; future database collation must be reviewed for Unicode equivalence. All-ASCII inventories avoid this ambiguity.'}
    baselineUnchanged=($baselineChanges.Count -eq 0); inventoryStableDuringCheck=($duringChanges.Count -eq 0)
    clean=($failed.Count -eq 0 -and $groupCount -eq 0 -and $baselineChanges.Count -eq 0 -and $duringChanges.Count -eq 0)
    imageDecodingChecked=$false
    limitations='Point-in-time reads, not an atomic NAS snapshot or proof of image decoding. Original baseline lacks full-file hashes, so historical byte equality cannot be established beyond recorded metadata and headers.'
}
Write-Evidence 'verification-summary.json' (($summary | ConvertTo-Json -Depth 6) + "`n")
Write-Evidence '.gitattributes' "* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`n"
$manifest = @(Get-ChildItem -LiteralPath $output -File -Force | Sort-Object Name | ForEach-Object { (Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant() + '  ' + $_.Name })
Write-Evidence 'SHA256SUMS.txt' (($manifest -join "`n") + "`n")
Write-Output "Verification complete: $($results.Count) files; $($failed.Count) read failures; $groupCount collision groups; clean=$($summary.clean). Evidence: $output"
