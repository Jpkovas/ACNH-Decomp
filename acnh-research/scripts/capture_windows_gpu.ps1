param(
 [ValidateRange(1,10000)][int]$Frame=500,
 [ValidateRange(1,300)][int]$Seconds=90
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$sdk=Join-Path $root 'private/tools/renderdoc/RenderDoc_1.46_64'
$runtime=Join-Path $root 'build/windows-bridge/vulkan/scarletnx.exe'
$game=Join-Path $root 'private/windows/bridge/ACNH_1_0_0'
$data=$game+'_data'
$captureDir=Join-Path $root 'private/windows/renderdoc-captures'
foreach($path in @((Join-Path $sdk 'renderdoccmd.exe'),$runtime,($game+'_code.dll'),(Join-Path $data 'romfs.bin'))){
 if(-not(Test-Path -LiteralPath $path)){throw "Missing capture prerequisite: $path"}
}
New-Item -ItemType Directory -Force -Path $captureDir | Out-Null
$prefix=Join-Path $captureDir ('ACNH-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
$names=@('VK_LAYER_PATH','VK_INSTANCE_LAYERS','ENABLE_VULKAN_RENDERDOC_CAPTURE','SNX_DATA_DIR','SNX_RENDERDOC_FRAME','SNX_RENDERDOC_OUTPUT')
$previous=@{}
foreach($name in $names){$previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
try{
 $env:VK_LAYER_PATH=$sdk
 $env:VK_INSTANCE_LAYERS='VK_LAYER_RENDERDOC_Capture'
 $env:ENABLE_VULKAN_RENDERDOC_CAPTURE='1'
 $env:SNX_DATA_DIR=$data
 $env:SNX_RENDERDOC_FRAME=[string]$Frame
 $env:SNX_RENDERDOC_OUTPUT=$prefix
 $argsList=@('capture','--wait-for-exit','--capture-file',"`"$prefix`"",'--working-dir',"`"$(Split-Path $game)`"",
   "`"$runtime`"","--game=`"$game`"","--seconds=$Seconds",'--headless','--fullscreen=0','--docked=1','--log=1')
 $process=Start-Process -FilePath (Join-Path $sdk 'renderdoccmd.exe') -ArgumentList $argsList -WindowStyle Hidden -PassThru -RedirectStandardOutput ($prefix+'.stdout.log') -RedirectStandardError ($prefix+'.stderr.log')
 $timer=[Diagnostics.Stopwatch]::StartNew()
 while(-not $process.HasExited){
  $process.WaitForExit(1000) | Out-Null
  if($timer.Elapsed.TotalSeconds -gt ($Seconds+90)){throw "Capture still running: helper PID $($process.Id), logs $prefix"}
 }
 $process.WaitForExit()
 $captures=@(Get-ChildItem -LiteralPath $captureDir -Filter ((Split-Path $prefix -Leaf)+'*.rdc'))
 $report=[ordered]@{frame=$Frame;seconds=$Seconds;exit_code=$process.ExitCode;
   captures=@($captures | ForEach-Object {$_.FullName});playable_validated=$false}
 $report | ConvertTo-Json | Set-Content -LiteralPath ($prefix+'.json') -Encoding utf8
 $report | ConvertTo-Json
 if($process.ExitCode -ne 0){throw "Capture helper exited with $($process.ExitCode)"}
 if($captures.Count -eq 0){throw 'No capture produced; confirm diagnostic SDK build and that the requested frame was reached'}
}finally{
 foreach($name in $names){[Environment]::SetEnvironmentVariable($name,$previous[$name],'Process')}
}
