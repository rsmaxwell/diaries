param(
    [Parameter(Mandatory=$true)][ValidateSet('disabled','enabled')][string]$Gate,
    [string]$ProjectRoot
)
. (Join-Path $PSScriptRoot 'step13-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot=[System.IO.Path]::GetFullPath($ProjectRoot)
$runDir=Get-CurrentStep13RunDirectory -ProjectRoot $ProjectRoot
$gateConfig=& (Join-Path $PSScriptRoot 'prepare-step13-gate-config.ps1') -Gate $Gate -ProjectRoot $ProjectRoot
if([string]::IsNullOrWhiteSpace([string]$gateConfig)){throw 'Could not prepare Step 13 responder gate config.'}
$previous=$env:DIARIES_RESPONDER_BASE_CONFIG_FILE
try{
    $env:DIARIES_RESPONDER_BASE_CONFIG_FILE=[string]$gateConfig
    $logPath=Join-Path $runDir ("responder-gate-"+$Gate+".log")
    Write-Host "Starting responder with imageFragmentWritesEnabled=$($Gate -eq 'enabled')"
    Write-Host "Responder output is also recorded at: $logPath"
    Write-Host 'The generated responder JSON stays under build/0027-step13 and must not be checked in.'
    & (Join-Path $ProjectRoot 'diaries-responder\scripts\windows\run-responder.bat') 2>&1 | Tee-Object -FilePath $logPath -Append
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){exit $exitCode}
} finally {
    if($null -eq $previous){Remove-Item Env:DIARIES_RESPONDER_BASE_CONFIG_FILE -ErrorAction SilentlyContinue}else{$env:DIARIES_RESPONDER_BASE_CONFIG_FILE=$previous}
}
