[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Step4Directory = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../../../..')).Path
$WindowsRoot = Join-Path $ProjectRoot 'scripts\windows'
$ValidationRoot = Join-Path $WindowsRoot 'validation'
$Step3Manifest = Join-Path $ProjectRoot 'change-control\in-progress\0032-FEAT - clean up completed-feature verification tooling from live script directories\evidence\Step 3\ARCHIVE-MANIFEST.csv'

function To-Relative([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = $ProjectRoot.TrimEnd('\') + '\'
    if (!$full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Path is outside project root: $full" }
    return $full.Substring($prefix.Length).Replace('\','/')
}

function Assert-Exists([string]$RelativePath) {
    $path = Join-Path $ProjectRoot $RelativePath
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required Step 4 successor is missing: $RelativePath"
    }
}

function Write-Inventory([string]$RootPath, [string]$OutputPath) {
    $lines = @('SHA256  PATH')
    Get-ChildItem -LiteralPath $RootPath -Recurse -File | Sort-Object FullName | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $lines += ('{0}  {1}' -f $hash, (To-Relative $_.FullName))
    }
    [IO.File]::WriteAllLines($OutputPath, $lines)
}

# The ZIP adds the successors before this script removes the obsolete names.
$successors = @(
    'scripts\windows\validation\imagefragment-image-http.cjs',
    'scripts\windows\validation\imagefragment-image-http.test.cjs',
    'scripts\windows\validation\imagefragment-proxy-routing.cjs',
    'scripts\windows\validation\imagefragment-proxy-routing.test.cjs',
    'scripts\windows\validation\imagefragment-retained-snapshot.cjs',
    'scripts\windows\validation\imagefragment-retained-snapshot.test.cjs',
    'scripts\windows\validation\verify-imagefragment-reader.ps1',
    'scripts\windows\validation\verify-effective-dataset-diagnostics.py',
    'scripts\windows\validation\verify-local-dataset-layout.py',
    'scripts\windows\validation\verify-direct-development-files-runtime.bat',
    'scripts\windows\validation\verify-direct-development-files-config.py',
    'scripts\windows\validation\verify-dataset-pair-guard.ps1',
    'scripts\windows\validation\verify-dataset-pair-guard.py',
    'scripts\windows\validation\verify-local-backup-restore-semantics.py'
)
$successors | ForEach-Object { Assert-Exists $_ }

if (!(Test-Path -LiteralPath $Step3Manifest -PathType Leaf)) {
    throw "Step 3 archive manifest is missing: $Step3Manifest"
}
$archiveRows = Import-Csv -LiteralPath $Step3Manifest
$archivedLiveFiles = @(
    'scripts/windows/0031-step10/seed-local-files-root.bat',
    'scripts/windows/0031-step10/seed-local-files-root.ps1',
    'scripts/windows/0031-step11/capture-local-mode.bat',
    'scripts/windows/0031-step11/capture-local-mode.ps1',
    'scripts/windows/0031-step11/compare-local-mode-evidence.ps1',
    'scripts/windows/0031-step12/compare-step9-step12.py',
    'scripts/windows/0031-step12/reconcile-common-pair.bat',
    'scripts/windows/0031-step12/reconcile-common-pair.ps1',
    'scripts/windows/0031-step13/run-local-lifecycle.bat',
    'scripts/windows/0031-step13/run-local-lifecycle.ps1',
    'scripts/windows/0031-step13/step13-rpc.cjs',
    'scripts/windows/0031-step16/rehearse-common-restore.bat',
    'scripts/windows/0031-step16/rehearse-common-restore.ps1',
    'scripts/windows/0031-step16/run-final-regression.bat',
    'scripts/windows/0031-step16/run-final-regression.ps1',
    'scripts/windows/0031-step8/capture-local-database-backup.bat',
    'scripts/windows/0031-step8/capture-local-database-backup.ps1',
    'scripts/windows/0031-step8/capture-shared-files-snapshot.bat',
    'scripts/windows/0031-step8/capture-shared-files-snapshot.ps1',
    'scripts/windows/0031-step8/freeze-local-writes.bat',
    'scripts/windows/0031-step8/freeze-local-writes.ps1',
    'scripts/windows/0031-step9/reconcile-local-shared-files.bat',
    'scripts/windows/0031-step9/reconcile-local-shared-files.ps1',
    'scripts/windows/validation/test-verify-0026-step14.py',
    'scripts/windows/validation/verify-0026-step14.ps1',
    'scripts/windows/validation/verify-0026-step14.py',
    'scripts/windows/validation/verify-0031-step10.py',
    'scripts/windows/validation/verify-0031-step13.py',
    'scripts/windows/validation/verify-0031-step16.py',
    'scripts/windows/validation/verify-0031-step8.py',
    'scripts/windows/validation/verify-0031-step9.py'
)
foreach ($relative in $archivedLiveFiles) {
    $row = $archiveRows | Where-Object { $_.'original repository' -eq 'diaries' -and $_.'original path' -eq $relative } | Select-Object -First 1
    if (!$row) { throw "Step 3 manifest does not preserve: $relative" }
    $archivePath = Join-Path $ProjectRoot $row.'archived path'
    if (!(Test-Path -LiteralPath $archivePath -PathType Leaf)) { throw "Archived copy is missing: $($row.'archived path')" }
    $actual = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $row.'SHA-256'.ToLowerInvariant()) { throw "Archived copy checksum mismatch: $($row.'archived path')" }
}

# Refuse to recursively remove a feature directory if it contains an unexpected file.
$expectedDirectoryFiles = @{
    '0031-step8'  = @('README.md','capture-local-database-backup.bat','capture-local-database-backup.ps1','capture-shared-files-snapshot.bat','capture-shared-files-snapshot.ps1','freeze-local-writes.bat','freeze-local-writes.ps1')
    '0031-step9'  = @('README.md','reconcile-local-shared-files.bat','reconcile-local-shared-files.ps1')
    '0031-step10' = @('README.md','seed-local-files-root.bat','seed-local-files-root.ps1')
    '0031-step11' = @('README.md','capture-local-mode.bat','capture-local-mode.ps1','compare-local-mode-evidence.ps1')
    '0031-step12' = @('compare-step9-step12.py','reconcile-common-pair.bat','reconcile-common-pair.ps1')
    '0031-step13' = @('README.md','run-local-lifecycle.bat','run-local-lifecycle.ps1','step13-rpc.cjs')
    '0031-step16' = @('README.md','rehearse-common-restore.bat','rehearse-common-restore.ps1','run-final-regression.bat','run-final-regression.ps1')
}
foreach ($name in $expectedDirectoryFiles.Keys) {
    $dir = Join-Path $WindowsRoot $name
    if (!(Test-Path -LiteralPath $dir -PathType Container)) { continue }
    $actualNames = @(Get-ChildItem -LiteralPath $dir -File | Select-Object -ExpandProperty Name | Sort-Object)
    $expectedNames = @($expectedDirectoryFiles[$name] | Sort-Object)
    if (($actualNames -join "`n") -ne ($expectedNames -join "`n")) {
        throw "Refusing to remove $name because its file set differs from the frozen Step 4 allow-list.`nActual: $($actualNames -join ', ')"
    }
    $subdirs = @(Get-ChildItem -LiteralPath $dir -Directory)
    if ($subdirs.Count -ne 0) { throw "Refusing to remove $name because it contains unexpected subdirectories." }
}

foreach ($name in $expectedDirectoryFiles.Keys) {
    $dir = Join-Path $WindowsRoot $name
    if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }
}

$oldValidationNames = @(
    'test-verify-0026-step14.py','verify-0026-step14.ps1','verify-0026-step14.py',
    'verify-0031-step10.py','verify-0031-step13.py','verify-0031-step16.py','verify-0031-step8.py','verify-0031-step9.py',
    'step13-image-http.cjs','step13-image-http.test.cjs','step13-proxy-routing.cjs','step13-proxy-routing.test.cjs',
    'step13-retained-snapshot.cjs','step13-retained-snapshot.test.cjs','verify-0026-step13.ps1','verify-0031-step11.py',
    'verify-0031-step3.py','verify-0031-step4-runtime.bat','verify-0031-step4.py','verify-0031-step6.ps1','verify-0031-step6.py','verify-0031-step7.py'
)
foreach ($name in $oldValidationNames) {
    $path = Join-Path $ValidationRoot $name
    if (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -Force }
}

Write-Inventory $WindowsRoot (Join-Path $Step4Directory 'WINDOWS-SCRIPTS-AFTER.txt')
Write-Inventory $ValidationRoot (Join-Path $Step4Directory 'WINDOWS-VALIDATION-AFTER.txt')

$patterns = @(
    'scripts/windows/0031-step','scripts\windows\0031-step','verify-0031-',
    'verify-0026-step13','verify-0026-step14','step13-image-http','step13-proxy-routing','step13-retained-snapshot'
)
$referenceLines = @()
Get-ChildItem -LiteralPath $WindowsRoot -Recurse -File | ForEach-Object {
    $file = $_
    foreach ($pattern in $patterns) {
        $matches = Select-String -LiteralPath $file.FullName -SimpleMatch -Pattern $pattern -ErrorAction Stop
        foreach ($match in $matches) {
            $referenceLines += ('{0}:{1}: {2}' -f (To-Relative $file.FullName), $match.LineNumber, $match.Line.Trim())
        }
    }
}
if ($referenceLines.Count -eq 0) {
    [IO.File]::WriteAllLines((Join-Path $Step4Directory 'REFERENCE-CHECK.txt'), @(
        'PASS: no retired 0031/0026 live path or filename references remain under scripts/windows.',
        'Checked patterns:',
        ($patterns | ForEach-Object { '  ' + $_ })
    ))
} else {
    [IO.File]::WriteAllLines((Join-Path $Step4Directory 'REFERENCE-CHECK.txt'), @('FAIL: retired references remain:') + $referenceLines)
    throw 'Retired Windows tooling references remain. See REFERENCE-CHECK.txt.'
}

$validationOutput = Join-Path $Step4Directory 'VALIDATION-OUTPUT.txt'
if (Test-Path -LiteralPath $validationOutput) { Remove-Item -LiteralPath $validationOutput -Force }
Start-Transcript -Path $validationOutput -Force | Out-Null
try {
    Push-Location $ProjectRoot
    try {
        function Invoke-NativeCheck([string]$Label, [string]$Command, [string[]]$Arguments) {
            Write-Host "`n>>> $Label"
            & $Command @Arguments
            if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE" }
        }

        Invoke-NativeCheck 'local dataset layout' 'python' @('scripts/windows/validation/verify-local-dataset-layout.py')
        Invoke-NativeCheck 'direct-development Files static contract' 'python' @('scripts/windows/validation/verify-direct-development-files-config.py')
        Invoke-NativeCheck 'dataset-pair portable contract' 'python' @('scripts/windows/validation/verify-dataset-pair-guard.py')
        Write-Host "`n>>> Windows dataset-pair exact guard cases"
        & (Join-Path $ValidationRoot 'verify-dataset-pair-guard.ps1')
        Invoke-NativeCheck 'local backup/restore semantics' 'python' @('scripts/windows/validation/verify-local-backup-restore-semantics.py')
        Invoke-NativeCheck 'effective dataset diagnostics' 'python' @('scripts/windows/validation/verify-effective-dataset-diagnostics.py')
        Invoke-NativeCheck 'ImageFragment retained-snapshot helper' 'node' @('--test','scripts/windows/validation/imagefragment-retained-snapshot.test.cjs')
        Invoke-NativeCheck 'ImageFragment Image HTTP helper' 'node' @('--test','scripts/windows/validation/imagefragment-image-http.test.cjs')
        Invoke-NativeCheck 'ImageFragment proxy-routing helper' 'node' @('--test','scripts/windows/validation/imagefragment-proxy-routing.test.cjs')
        Invoke-NativeCheck 'direct-development Files runtime contract' 'cmd.exe' @('/d','/c','scripts\windows\validation\verify-direct-development-files-runtime.bat')

        Write-Host "`nPASS: Step 4 Windows cleanup and retained regression verification completed."
    }
    finally { Pop-Location }
}
finally { Stop-Transcript | Out-Null }

Write-Host "Step 4 cleanup/verification evidence written to: $Step4Directory"
