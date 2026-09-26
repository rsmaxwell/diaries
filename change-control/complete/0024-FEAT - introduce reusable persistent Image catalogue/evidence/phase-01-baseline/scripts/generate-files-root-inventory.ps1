[CmdletBinding()]
param(
    [string]$FilesRoot = 'P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files',
    [string]$OutputFile,
    [string]$SummaryFile
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($OutputFile)) {
    $OutputFile = Join-Path $PSScriptRoot '..\files-root-inventory.detected.csv'
}
$root = Get-Item -LiteralPath $FilesRoot -Force
if ($root.PSProvider.Name -ne 'FileSystem' -or !$root.PSIsContainer) {
    throw 'FilesRoot must be a filesystem directory.'
}

# GetRelativePath is unavailable in Windows PowerShell 5.1. Remove the verified
# directory prefix instead. Including the separator prevents sibling matches.
$rootPrefix = $root.FullName.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
$outputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputFile)
if (Test-Path -LiteralPath $outputPath) {
    throw "Output already exists; choose a new filename to preserve it: $outputPath"
}
if ($outputPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'OutputFile must be outside the Files root being inventoried.'
}
if ([string]::IsNullOrWhiteSpace($SummaryFile)) { $SummaryFile = [IO.Path]::ChangeExtension($outputPath, '.summary.json') }
$summaryPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SummaryFile)
if ($summaryPath.Equals($outputPath, [StringComparison]::OrdinalIgnoreCase) -or
    $summaryPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'SummaryFile must be separate from the CSV and outside the Files root.' }
if (Test-Path -LiteralPath $summaryPath) { throw "Summary already exists; choose a new filename: $summaryPath" }

function Test-HeaderSignature {
    param([byte[]]$Header, [int]$BytesRead, [byte[]]$Signature, [int]$Offset = 0)
    if ($BytesRead -lt ($Offset + $Signature.Length)) { return $false }
    for ($i = 0; $i -lt $Signature.Length; $i++) {
        if ($Header[$Offset + $i] -ne $Signature[$i]) { return $false }
    }
    return $true
}

function Get-ImageSignature {
    param([IO.FileInfo]$File)
    $result = [ordered]@{
        detectedMimeType = ''
        signatureStatus = 'NO_SUPPORTED_SIGNATURE'
        headerBytesRead = 0
        headerHex = ''
        extensionStatus = 'NOT_APPLICABLE'
        inspectionError = ''
    }
    $header = New-Object byte[] 16
    $inputStream = $null
    try {
        $inputStream = [IO.File]::Open($File.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        while ($result.headerBytesRead -lt $header.Length) {
            $read = $inputStream.Read($header, $result.headerBytesRead, $header.Length - $result.headerBytesRead)
            if ($read -eq 0) { break }
            $result.headerBytesRead += $read
        }
        $result.headerHex = [BitConverter]::ToString($header, 0, $result.headerBytesRead).Replace('-', '').ToLowerInvariant()
    } catch {
        $result.signatureStatus = 'UNREADABLE'
        $result.inspectionError = $_.Exception.GetBaseException().Message
        return [pscustomobject]$result
    } finally {
        if ($inputStream) { $inputStream.Dispose() }
    }

    # Content signatures only: https://mimesniff.spec.whatwg.org/#matching-an-image-type-pattern
    # WebP also requires a recognized first chunk (VP8, VP8L or VP8X).
    # A recognized header identifies a candidate; it does not validate image decoding.
    $count = $result.headerBytesRead
    if (Test-HeaderSignature $header $count ([byte[]]@(0xff, 0xd8, 0xff))) {
        $result.detectedMimeType = 'image/jpeg'
    } elseif (Test-HeaderSignature $header $count ([byte[]]@(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a))) {
        $result.detectedMimeType = 'image/png'
    } elseif ((Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('GIF87a'))) -or
              (Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('GIF89a')))) {
        $result.detectedMimeType = 'image/gif'
    } elseif ((Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('RIFF'))) -and
              (Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('WEBP')) 8) -and
              ((Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('VP8 ')) 12) -or
               (Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('VP8L')) 12) -or
               (Test-HeaderSignature $header $count ([Text.Encoding]::ASCII.GetBytes('VP8X')) 12))) {
        $result.detectedMimeType = 'image/webp'
    }
    $extensionTypes = @{'.jpg'='image/jpeg'; '.jpeg'='image/jpeg'; '.png'='image/png'; '.gif'='image/gif'; '.webp'='image/webp'}
    $extensionMimeType = $extensionTypes[$File.Extension.ToLowerInvariant()]
    if ($result.detectedMimeType) {
        $result.signatureStatus = 'IMAGE_SIGNATURE'
        $result.extensionStatus = $(if ($extensionMimeType -eq $result.detectedMimeType) { 'MATCH' } else { 'MISMATCH' })
    } elseif ($extensionMimeType) {
        $result.extensionStatus = 'MISMATCH'
    }
    return [pscustomobject]$result
}

function Get-InventoryEntries {
    param([string]$Directory)
    # Never descend into directory symlinks/junctions or inspect linked files.
    $pending = New-Object 'Collections.Generic.Stack[string]'
    $pending.Push($Directory)
    while ($pending.Count -gt 0) {
        foreach ($entry in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            Write-Output $entry
            if ($entry.PSIsContainer -and !($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                $pending.Push($entry.FullName)
            }
        }
    }
}

# Select-Object can hide calculated-property exceptions as blank cells.
# Calculate and validate all rows explicitly before writing the report.
$rows = @(Get-InventoryEntries $root.FullName | ForEach-Object {
    $entry = $_
    if (!$entry.FullName.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Entry is outside the expected root: $($entry.FullName)"
    }
    $relativePath = $entry.FullName.Substring($rootPrefix.Length).Replace('\', '/')
    if ([string]::IsNullOrWhiteSpace($relativePath)) {
        throw "Cannot calculate a relative path: $($entry.FullName)"
    }
    $isLink = [bool]($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)
    $inspection = if (!$entry.PSIsContainer -and !$isLink) { Get-ImageSignature $entry } else { $null }
    [pscustomobject]@{
        relativePath = $relativePath
        entryType = $(if ($isLink) { 'link' } elseif ($entry.PSIsContainer) { 'directory' } else { 'file' })
        Length = $(if ($entry.PSIsContainer) { $null } else { $entry.Length })
        Extension = $entry.Extension
        lastModifiedUtc = $entry.LastWriteTimeUtc.ToString('o')
        LinkType = $entry.LinkType
        detectedMimeType = $(if ($inspection) { $inspection.detectedMimeType } else { '' })
        signatureStatus = $(if ($inspection) { $inspection.signatureStatus } elseif ($isLink) { 'SKIPPED_LINK' } else { 'NOT_APPLICABLE' })
        headerBytesRead = $(if ($inspection) { $inspection.headerBytesRead } else { 0 })
        headerHex = $(if ($inspection) { $inspection.headerHex } else { '' })
        extensionStatus = $(if ($inspection) { $inspection.extensionStatus } else { 'NOT_APPLICABLE' })
        inspectionError = $(if ($inspection) { $inspection.inspectionError } else { '' })
    }
} | Sort-Object relativePath)

# Emit a header even for an empty root. CreateNew prevents overwriting evidence.
$csv = @('"relativePath","entryType","Length","Extension","lastModifiedUtc","LinkType","detectedMimeType","signatureStatus","headerBytesRead","headerHex","extensionStatus","inspectionError"')
if ($rows.Count -gt 0) { $csv = @($rows | ConvertTo-Csv -NoTypeInformation) }
$stream = [IO.File]::Open($outputPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    $writer = New-Object IO.StreamWriter($stream, (New-Object Text.UTF8Encoding($false)))
    try { foreach ($line in $csv) { $writer.WriteLine($line) } }
    finally { $writer.Dispose() }
} finally { $stream.Dispose() }

Write-Output "Wrote $($rows.Count) entries with nonblank relative paths to $outputPath"
& (Join-Path $PSScriptRoot 'summarize-files-root-inventory.ps1') -InventoryFile $outputPath -SummaryFile $summaryPath
