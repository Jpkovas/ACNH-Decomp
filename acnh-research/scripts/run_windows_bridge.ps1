param(
 [ValidateSet('native','probe')][string]$Mode='native',
 [ValidateRange(1,1800)][int]$Seconds=30,
 [switch]$Headless,
 [string]$InputScript='',
 [ValidateRange(1,10000)][int]$PressLength=300,
 [ValidateRange(0,10000)][int]$ShotEvery=0,
 [switch]$CaptureShaders,
 [switch]$CaptureTargets,
 [ValidateSet(0,1)][int]$Docked=1
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$runtime=Join-Path $root 'build/windows-bridge/vulkan/scarletnx.exe'
$game=if($Mode -eq 'native'){Join-Path $root 'private/windows/bridge/ACNH_1_0_0'}else{Join-Path $root 'private/windows/probe/ACNH_probe'}
$data=Join-Path $root 'private/windows/bridge/ACNH_1_0_0_data'
if(-not(Test-Path -LiteralPath ($game+'_code.dll'))){throw "Missing $Mode code module"}
if(-not(Test-Path -LiteralPath (Join-Path $data 'romfs.bin'))){throw 'Prepare the single-file RomFS first'}
$env:SNX_DATA_DIR=$data
$logs=Join-Path $root 'private/windows/logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$prefix=Join-Path $logs ("{0}-{1}" -f $Mode,(Get-Date -Format 'yyyyMMdd-HHmmss'))
if($CaptureTargets){
 $env:SNX_RT_DUMP_DIR=$prefix+'-targets'
 New-Item -ItemType Directory -Force -Path $env:SNX_RT_DUMP_DIR | Out-Null
}else{Remove-Item Env:SNX_RT_DUMP_DIR -ErrorAction SilentlyContinue}
$arguments=@("--game=$game","--seconds=$Seconds",'--log=1','--fullscreen=0',"--docked=$Docked","--shot=$prefix","--press_len=$PressLength","--shot_every=$ShotEvery")
if($Headless){$arguments+='--headless'}
if($InputScript){$arguments+="--script=$InputScript"}
if($CaptureShaders){
 $env:SNX_SHADER_CORPUS=Join-Path $root 'private/windows/shader-corpus'
 New-Item -ItemType Directory -Force -Path $env:SNX_SHADER_CORPUS | Out-Null
}
else{Remove-Item Env:SNX_SHADER_CORPUS -ErrorAction SilentlyContinue}
$process=Start-Process -FilePath $runtime -ArgumentList $arguments -WorkingDirectory (Split-Path $game) -WindowStyle Hidden -PassThru -RedirectStandardOutput ($prefix+'.stdout.log') -RedirectStandardError ($prefix+'.stderr.log')
$timer=[Diagnostics.Stopwatch]::StartNew()
$limit=$Seconds+90
while(-not $process.HasExited){
 $process.WaitForExit(1000) | Out-Null
 if($timer.Elapsed.TotalSeconds -gt $limit){
  Stop-Process -Id $process.Id
  throw "Diagnostic timed out; logs: $prefix"
 }
}
$process.WaitForExit()
$result=[ordered]@{mode=$Mode;headless=[bool]$Headless;docked=$Docked;input_script=$InputScript;press_length_ms=$PressLength;shot_every_frames=$ShotEvery;exit_code=$process.ExitCode;elapsed_seconds=[math]::Round($timer.Elapsed.TotalSeconds,2);stdout=$prefix+'.stdout.log';stderr=$prefix+'.stderr.log';game_log=$game+'.log';screenshot=if(Test-Path -LiteralPath ($prefix+'.ppm')){$prefix+'.ppm'}else{$null};playable_validated=$false}
$result | ConvertTo-Json | Set-Content -LiteralPath ($prefix+'.json') -Encoding utf8
$result | ConvertTo-Json
Select-String -LiteralPath ($prefix+'.stdout.log'),($prefix+'.stderr.log') -Pattern 'RomFS:|vulkan:|FATAL:|Unsupported instruction|svcBreak|frames=' | Select-Object -First 12 | ForEach-Object {$_.Line}
if($process.ExitCode -ne 0){exit $process.ExitCode}
