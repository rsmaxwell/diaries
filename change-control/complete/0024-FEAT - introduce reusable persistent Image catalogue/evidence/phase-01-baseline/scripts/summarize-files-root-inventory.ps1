[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InventoryFile,
    [Parameter(Mandatory)][string]$SummaryFile,
    [switch]$ReplaceEmptyOutput
)
$ErrorActionPreference = 'Stop'
$inventoryPath = (Resolve-Path -LiteralPath $InventoryFile).Path
$summaryPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SummaryFile)
if ($inventoryPath.Equals($summaryPath, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'SummaryFile must not be the inventory file.'
}
if ((Test-Path -LiteralPath $summaryPath) -and (!$ReplaceEmptyOutput -or (Get-Item -LiteralPath $summaryPath).Length -ne 0)) {
    throw 'Summary output already exists. Only an empty placeholder may be explicitly replaced.'
}

# Hash before and after parsing so the summary cannot describe a changing CSV.
$inventoryHash = (Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
$expectedHeader = '"relativePath","entryType","Length","Extension","lastModifiedUtc","LinkType","detectedMimeType","signatureStatus","headerBytesRead","headerHex","extensionStatus","inspectionError"'
if ((Get-Content -LiteralPath $inventoryPath -Encoding UTF8 -TotalCount 1) -cne $expectedHeader) {
    throw 'Expected the signature-aware inventory CSV schema; regenerate older inventories first.'
}
$rows = @(Import-Csv -LiteralPath $inventoryPath -Encoding UTF8)
$paths = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
$types = [ordered]@{'image/jpeg'=0; 'image/png'=0; 'image/gif'=0; 'image/webp'=0}
$regularFiles = 0; $directories = 0; $links = 0; [long]$totalBytes = 0
foreach ($row in $rows) {
    if ([string]::IsNullOrWhiteSpace($row.relativePath) -or !$paths.Add($row.relativePath)) {
        throw 'Inventory contains a blank or duplicate exact relative path.'
    }
    if ($row.entryType -eq 'directory') {
        if ($row.signatureStatus -ne 'NOT_APPLICABLE') { throw 'Invalid directory inspection status.' }
        $directories++
    } elseif ($row.entryType -eq 'link') {
        if ($row.signatureStatus -ne 'SKIPPED_LINK') { throw 'Invalid link inspection status.' }
        $links++
    } elseif ($row.entryType -eq 'file') {
        $regularFiles++
        [long]$length = 0; [int]$bytesRead = 0
        if (![long]::TryParse($row.Length, [ref]$length) -or $length -lt 0 -or
            ![int]::TryParse($row.headerBytesRead, [ref]$bytesRead) -or $bytesRead -lt 0 -or $bytesRead -gt 16) {
            throw 'Invalid file length or inspected header length.'
        }
        $totalBytes += $length
        if ($row.signatureStatus -eq 'IMAGE_SIGNATURE') {
            if (!$types.Contains($row.detectedMimeType)) { throw 'Unknown detected image MIME type.' }
            $types[$row.detectedMimeType]++
        } elseif ($row.signatureStatus -notin @('NO_SUPPORTED_SIGNATURE', 'UNREADABLE')) {
            throw 'Missing or unknown regular-file inspection status.'
        } elseif ($row.detectedMimeType) {
            throw 'An unrecognized/unreadable file must not claim a detected MIME type.'
        }
        if ($row.extensionStatus -notin @('MATCH', 'MISMATCH', 'NOT_APPLICABLE')) { throw 'Unknown extension status.' }
        if ($row.signatureStatus -eq 'UNREADABLE' -and [string]::IsNullOrWhiteSpace($row.inspectionError)) {
            throw 'Unreadable file lacks an inspection error.'
        }
    } else { throw 'Unknown inventory entry type.' }
}
if ((Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $inventoryHash) {
    throw 'Inventory changed while the summary was being generated.'
}
$candidates = @($rows | Where-Object signatureStatus -eq 'IMAGE_SIGNATURE')
$unsupported = @($rows | Where-Object signatureStatus -eq 'NO_SUPPORTED_SIGNATURE')
$unreadable = @($rows | Where-Object signatureStatus -eq 'UNREADABLE')
$mismatches = @($rows | Where-Object extensionStatus -eq 'MISMATCH')
if ($regularFiles -ne ($candidates.Count + $unsupported.Count + $unreadable.Count)) { throw 'File categories do not reconcile.' }
$summary = [ordered]@{
    schemaVersion = 1
    generatedAtUtc = [DateTime]::UtcNow.ToString('o')
    source = [ordered]@{
        inventoryFile = [IO.Path]::GetFileName($inventoryPath)
        inventorySha256 = $inventoryHash
        inventoryBytes = (Get-Item -LiteralPath $inventoryPath).Length
        sourceScanTimestamp = $null
        note = 'Derived from the saved CSV; generation time is not a new NAS scan time. The CSV does not record the original scan timestamp.'
    }
    totals = [ordered]@{
        entries = $rows.Count
        regularFiles = $regularFiles
        directoriesExcludingRoot = $directories
        symlinksOrReparsePoints = $links
        regularFileBytesFromMetadata = $totalBytes
        imageCandidates = $candidates.Count
        filesWithoutSupportedImageSignature = $unsupported.Count
        unreadableHeaders = $unreadable.Count
        extensionMismatches = $mismatches.Count
        blankRelativePaths = 0
        duplicateExactRelativePaths = 0
    }
    imageCandidatesByDetectedMimeType = $types
    headerInspection = [ordered]@{
        maximumBytesPerFile = 16
        readableRegularFileHeaders = $regularFiles - $unreadable.Count
        fullFileReadabilityChecked = $false
        fullFileUnreadableCount = $null
        imageDecodingChecked = $false
        note = 'Recognized signatures identify candidates, not validated/decodable images. Links are not followed.'
    }
    caseFoldedPathCollisions = [ordered]@{checked=$false; groupCount=$null; note='Exact-path uniqueness is checked above; a case-folded collision report has not been generated.'}
    filesWithoutSupportedImageSignature = @($unsupported | Sort-Object relativePath | Select-Object -ExpandProperty relativePath)
    unreadableHeaders = @($unreadable | Sort-Object relativePath | Select-Object relativePath,inspectionError)
    extensionMismatches = @($mismatches | Sort-Object relativePath | Select-Object relativePath,Extension,detectedMimeType)
    skippedLinks = @($rows | Where-Object entryType -eq 'link' | Sort-Object relativePath | Select-Object relativePath,LinkType)
    remainingInventoryEvidence = @('Full-file readability verification', 'Case-folded path collision report')
}
$json = ($summary | ConvertTo-Json -Depth 8) + "`n"
$mode = if ($ReplaceEmptyOutput -and (Test-Path -LiteralPath $summaryPath)) { [IO.FileMode]::Open } else { [IO.FileMode]::CreateNew }
$stream = [IO.File]::Open($summaryPath, $mode, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    if ($stream.Length -ne 0) { throw 'Refusing to overwrite nonempty summary output.' }
    $writer = New-Object IO.StreamWriter($stream, (New-Object Text.UTF8Encoding($false)))
    try { $writer.Write($json) } finally { $writer.Dispose() }
} finally { $stream.Dispose() }
Write-Output "Wrote summary for $($rows.Count) entries ($regularFiles files) to $summaryPath"
