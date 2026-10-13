param(
 [ValidateSet('base','update')][string]$Package='base',
 [ValidateSet('import','analyze','export','reimport','verify','baseline','curated')][string]$Mode='import'
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$ghidra=Join-Path $root 'private/tools/ghidra/ghidra_12.1.4_PUBLIC'
$jdk=Get-ChildItem -LiteralPath (Join-Path $root 'private/tools/jdk') -Directory | Select-Object -First 1
$env:JAVA_HOME=$jdk.FullName
$env:GHIDRA_HEADLESS_MAXMEM='8G'
$version=if($Package -eq 'base'){'1.0.0'}else{'3.0.3'}
$project='acnh_'+$Package
if($Mode -in @('reimport','verify')){$project+='_reimport'}
if($Mode -in @('baseline','curated','export')){$project+='_baseline'}
$env:GHIDRA_HEADLESS_JAVA_OPTIONS="-Dapplication.settingsdir=$root/private/ghidra-settings/$project -Dapplication.cachedir=$root/private/ghidra-cache/$project -Dapplication.tempdir=$root/private/ghidra-temp/$project"
$output=Join-Path $root ('private/outputs/'+$version+'/ghidra')
if($Mode -eq 'reimport'){$output=Join-Path $root ('private/outputs/'+$version+'/ghidra-reimport')}
New-Item -ItemType Directory -Path $output -Force | Out-Null
$arguments=@((Join-Path $root 'private/ghidra'),$project)
if($Mode -eq 'baseline'){
 $arguments+=@('-import',(Join-Path $root ('private/inputs/extracted/'+$Package+'/exefs/main')),'-overwrite','-preScript','ConfigureBaseline.java',(Join-Path $output 'analysis-profile.json'))
}elseif($Mode -in @('import','reimport')){
 $arguments+=@('-import',(Join-Path $root ('private/inputs/extracted/'+$Package+'/exefs/main')),'-noanalysis')
 if($Mode -eq 'reimport'){$arguments+='-overwrite'}
}else{
 $arguments+=@('-process','main')
 if($Mode -in @('export','verify','curated')){$arguments+='-noanalysis'}
}
if($Mode -eq 'verify'){
 $arguments+=@('-scriptPath',(Join-Path $root 'ghidra_scripts'),'-postScript','VerifyRelativeRelocations.java',(Join-Path $root ('private/outputs/'+$version+'/nxo/relative-relocations.tsv')),(Join-Path $root ('metadata/'+$version+'/relocation-verification.json')),$version)
}elseif($Mode -eq 'curated'){
 $arguments+=@('-scriptPath',(Join-Path $root 'ghidra_scripts'),'-postScript','ImportValidatedSymbols.java',(Join-Path $root ('metadata/'+$version+'/reviewed-annotations.json')),(Join-Path $root ('metadata/'+$version+'/annotation-import.json')),'-postScript','ExportResearchInventory.java',$output,$version)
}else{
 $arguments+=@('-scriptPath',(Join-Path $root 'ghidra_scripts'),'-postScript','ExportResearchInventory.java',$output,$version)
}
if($Mode -in @('import','reimport')){$arguments+='layout-only'}
$runLog=Join-Path $output ($Mode+'-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.log')
$arguments+=@('-max-cpu','4','-analysisTimeoutPerFile','7200','-log',$runLog)
& (Join-Path $ghidra 'support/analyzeHeadless.bat') @arguments
if($LASTEXITCODE -ne 0){throw "Ghidra $Mode failed"}
if((Get-Content -LiteralPath $runLog -Raw) -match 'REPORT SCRIPT ERROR|Error creating bundle cache|Import failed'){throw 'Ghidra script, import or bundle initialization failed; see local log'}
if(-not(Test-Path -LiteralPath (Join-Path $output 'import-layout.json'))){throw 'Ghidra export script did not produce its expected artifact'}
