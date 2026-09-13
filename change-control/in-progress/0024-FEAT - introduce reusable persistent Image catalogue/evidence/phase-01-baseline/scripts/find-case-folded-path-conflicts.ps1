[CmdletBinding()]
param([Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Rows)
$ErrorActionPreference = 'Stop'
# Explicit ordinal grouping avoids PowerShell's culture-sensitive grouping.
$groups = New-Object 'Collections.Generic.Dictionary[string,Collections.Generic.List[object]]' ([StringComparer]::Ordinal)
foreach ($row in $Rows) {
    $path = [string]$row.relativePath
    if ([string]::IsNullOrWhiteSpace($path) -or $path -match '(^[/\\]|:|(^|[/\\])\.\.?([/\\]|$)|[/\\]$|[/\\]{2})') {
        throw "Invalid inventory relative path: $path"
    }
    $key = $path.Replace('\','/').Normalize([Text.NormalizationForm]::FormC).ToLowerInvariant()
    if (!$groups.ContainsKey($key)) { $groups.Add($key, (New-Object 'Collections.Generic.List[object]')) }
    $groups[$key].Add($row)
}
foreach ($key in @($groups.Keys | Sort-Object)) {
    if ($groups[$key].Count -gt 1) {
        foreach ($row in $groups[$key]) {
            [pscustomobject]@{foldedPath=$key; relativePath=$row.relativePath; entryType=$row.entryType; groupSize=$groups[$key].Count}
        }
    }
}
