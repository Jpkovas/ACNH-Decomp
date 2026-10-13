param([switch]$RegenerateData,[switch]$AnalyzeBinaries)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python=Join-Path $root 'private/tools/python/python.exe'
function Invoke-Python([string]$Script,[string[]]$Arguments=@()) {
 & $python (Join-Path $PSScriptRoot $Script) @Arguments
 if($LASTEXITCODE -ne 0){throw "Pipeline step failed: $Script"}
}
$logDir=Join-Path $root 'private/outputs/pipeline'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log=Join-Path $logDir ((Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
Start-Transcript -LiteralPath $log | Out-Null
try {
 if(-not $AnalyzeBinaries){
  foreach($version in @('1.0.0','3.0.3')){
   if(-not(Test-Path -LiteralPath (Join-Path $root ('private/outputs/'+$version+'/ghidra/inventory-summary.json')))){throw "Complete Ghidra baseline required: $version"}
  }
 }
 & (Join-Path $PSScriptRoot 'build_native.ps1') -Compiler clang
 Invoke-Python 'run_python_tests.py'
 if($AnalyzeBinaries){
  foreach($package in @('base','update')){
   & (Join-Path $PSScriptRoot 'run_ghidra.ps1') -Package $package -Mode baseline
   & (Join-Path $PSScriptRoot 'run_ghidra.ps1') -Package $package -Mode reimport
   & (Join-Path $PSScriptRoot 'run_ghidra.ps1') -Package $package -Mode verify
  }
 }
 if($RegenerateData){
  foreach($item in @(@('base','1.0.0'),@('update','3.0.3'))){
   $romfs=Join-Path $root ('private/inputs/extracted/'+$item[0]+'/romfs')
   foreach($script in @('catalog_bcsv.py','eventflow_catalog.py','catalog_resources.py','validate_save_schemas.py','catalog_semantics.py')){
    Invoke-Python $script @($romfs,'--version-id',$item[1])
   }
   Invoke-Python 'eventflow_roundtrip.py' @((Join-Path $romfs 'EventFlow/AI_NPC_Doc_Airport.bfevfl'),'--version-id',$item[1])
   Invoke-Python 'validate_bcsv.py' @($romfs,'--version-id',$item[1])
  }
  Invoke-Python 'matching_pilot.py'
  Invoke-Python 'validate_identifier_hash.py'
  Invoke-Python 'validate_identifier_hash.py' @('--version-id','3.0.3')
  Invoke-Python 'catalog_factory_bindings.py'
  Invoke-Python 'catalog_factory_bindings.py' @('--version-id','3.0.3')
  Invoke-Python 'validate_flag_int.py'
  Invoke-Python 'validate_flag_int.py' @('--version-id','3.0.3')
 }
 Invoke-Python 'finalize_provenance.py'
 foreach($item in @(@('base','1.0.0'),@('update','3.0.3'))){
  $notes=Join-Path $root ('metadata/'+$item[1]+'/reviewed-annotations.json')
  $importReport=Join-Path $root ('metadata/'+$item[1]+'/annotation-import.json')
  $notesHash=(Get-FileHash -LiteralPath $notes -Algorithm SHA256).Hash.ToLowerInvariant()
  $appliedHash=if(Test-Path -LiteralPath $importReport){(Get-Content -LiteralPath $importReport -Raw|ConvertFrom-Json).annotations_sha256}else{''}
  if($notesHash -ne $appliedHash){& (Join-Path $PSScriptRoot 'run_ghidra.ps1') -Package $item[0] -Mode curated}
 }
 foreach($version in @('1.0.0','3.0.3')){Invoke-Python 'normalize_symbols.py' @('--version-id',$version)}
 Invoke-Python 'map_versions.py'
 Invoke-Python 'verify_golden.py'
 Invoke-Python 'collect_metrics.py'
 Invoke-Python 'audit_research.py'
 $result=@{completed=$true;utc=(Get-Date).ToUniversalTime().ToString('o');regenerated_data=[bool]$RegenerateData;analyzed_binaries=[bool]$AnalyzeBinaries;log=$log}
 $result|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'metadata/pipeline-verification.json') -Encoding utf8
} finally {Stop-Transcript | Out-Null}
