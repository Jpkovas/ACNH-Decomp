param([switch]$Regenerate)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python=Join-Path $root 'private/tools/python/python.exe'
$source=Join-Path $root 'private/inputs/extracted/base/exefs'
$tool=Join-Path $root 'build/windows-bridge/tools/scarletnx.exe'
$input=Join-Path $root 'private/windows/input-1.0.0'
$generation=Join-Path $root 'private/windows/generation'
$output=Join-Path $root 'private/windows/bridge'
$generated=Join-Path $output 'ACNH_1_0_0_build'
if((Test-Path -LiteralPath (Join-Path $generated 'module.c')) -and -not $Regenerate){
 Write-Output 'Private generated sources already exist; use -Regenerate to rebuild them.'
 exit 0
}
& $python (Join-Path $root 'scripts/profile_exefs.py') --version-id 1.0.0 --exefs $source
if($LASTEXITCODE -ne 0){throw 'ExeFS profile validation failed'}
New-Item -ItemType Directory -Force -Path $input,$generation,$generated,(Join-Path $root 'private/windows/tmp') | Out-Null
Get-ChildItem -LiteralPath $source -File | ForEach-Object {
 Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $input $_.Name)
}
$hints=Join-Path $output 'ACNH_1_0_0.hints'
if(Test-Path -LiteralPath $hints){Copy-Item -LiteralPath $hints -Destination (Join-Path $generation 'ACNH_1_0_0.hints')}
$env:TEMP=Join-Path $root 'private/windows/tmp'
$env:TMP=$env:TEMP
# Use a separate output directory: the upstream driver rejects a cached raw
# RomFS for NSO input. The runtime accepts the independently verified image.
& $tool --recompile $input ACNH_1_0_0 --outdir $generation --no-build
if($LASTEXITCODE -ne 0){throw 'Private code generation failed'}
$stage=Join-Path $generation 'ACNH_1_0_0_build'
Get-ChildItem -LiteralPath $stage -File -Filter '*.c' | ForEach-Object {
 $destination=Join-Path $generated $_.Name
 Move-Item -LiteralPath $_.FullName -Destination $destination -Force
}
$exefs=Join-Path $output 'ACNH_1_0_0_data/exefs'
New-Item -ItemType Directory -Force -Path $exefs | Out-Null
Get-ChildItem -LiteralPath $input -File | ForEach-Object {
 Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $exefs $_.Name)
}
