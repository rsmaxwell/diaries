param(
    [Parameter(Mandatory=$true)][ValidateSet('disabled','enabled')][string]$Gate,
    [string]$ProjectRoot,
    [string]$SourceConfig
)
. (Join-Path $PSScriptRoot 'step13-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot=[System.IO.Path]::GetFullPath($ProjectRoot)
if([string]::IsNullOrWhiteSpace($SourceConfig)){ $SourceConfig=Join-Path $env:USERPROFILE '.diaries\responder.json' }
$SourceConfig=[System.IO.Path]::GetFullPath($SourceConfig)
if(-not (Test-Path -LiteralPath $SourceConfig -PathType Leaf)){throw "Responder base config not found: $SourceConfig"}
$config=Get-Content -LiteralPath $SourceConfig -Raw | ConvertFrom-Json
$enabled=($Gate -eq 'enabled')
if($null -eq $config.PSObject.Properties['imageFragmentWritesEnabled']){
    $config | Add-Member -NotePropertyName imageFragmentWritesEnabled -NotePropertyValue $enabled
}else{$config.imageFragmentWritesEnabled=$enabled}
$outDir=Join-Path (Get-Step13BuildRoot -ProjectRoot $ProjectRoot) ("gate-"+$Gate)
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outPath=Join-Path $outDir 'responder.base.json'
$json=$config | ConvertTo-Json -Depth 100
Write-Utf8NoBom -Path $outPath -Text ($json+[Environment]::NewLine)
# Deliberately emit only the path. The generated config contains local secrets and stays under ignored build/.
Write-Output $outPath
