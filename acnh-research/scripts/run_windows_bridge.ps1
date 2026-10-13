param(
 [ValidateSet('native','probe')][string]$Mode='native',
 [ValidateRange(1,1800)][int]$Seconds=30,
 [switch]$Headless,
 [string]$InputScript='',
 [ValidateRange(1,10000)][int]$PressLength=300,
 [ValidateRange(0,10000)][int]$ShotEvery=0,
 [switch]$LiveInput,
 [switch]$CaptureAudioInputs,
 [switch]$NativeAudio,
 [switch]$AudioWavOnly,
 [switch]$CaptureShaders,
 [switch]$CaptureTargets,
 [switch]$CaptureGpuFifo,
 [switch]$CaptureGraphics,
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
if($CaptureGraphics){
 $captureSdk=Join-Path $root 'private/tools/renderdoc/RenderDoc_1.46_64'
 if(-not(Test-Path -LiteralPath (Join-Path $captureSdk 'renderdoc.dll'))){throw 'Missing pinned RenderDoc SDK'}
 $env:VK_LAYER_PATH=$captureSdk
 $env:VK_INSTANCE_LAYERS='VK_LAYER_RENDERDOC_Capture'
 $env:ENABLE_VULKAN_RENDERDOC_CAPTURE='1'
 $env:SNX_RENDERDOC_OUTPUT=$prefix+'-graphics'
 $env:SNX_RENDERDOC_TRIGGER=$prefix+'.capture.txt'
 Remove-Item Env:SNX_RENDERDOC_FRAME -ErrorAction SilentlyContinue
 Set-Content -LiteralPath $env:SNX_RENDERDOC_TRIGGER -Value '0' -Encoding ascii
 Write-Output "GPU capture trigger: $env:SNX_RENDERDOC_TRIGGER"
}else{Remove-Item Env:SNX_RENDERDOC_TRIGGER,Env:SNX_RENDERDOC_OUTPUT,Env:SNX_RENDERDOC_FRAME -ErrorAction SilentlyContinue}
if($CaptureGpuFifo){
 $env:SNX_FIFO_TRACE_DIR=$prefix+'-fifo'
 New-Item -ItemType Directory -Force -Path $env:SNX_FIFO_TRACE_DIR | Out-Null
}else{Remove-Item Env:SNX_FIFO_TRACE_DIR -ErrorAction SilentlyContinue}
if($NativeAudio){
 $env:SNX_AUDIO_BACKEND=Join-Path $root 'private/windows/audio/ACNH_audio.dll'
 if(-not(Test-Path -LiteralPath $env:SNX_AUDIO_BACKEND)){throw 'Build the native audio module first'}
 $env:SNX_AUDIO_WAV=$prefix+'.wav'
 $env:SNX_AUDIO_WAV_ONLY=if($AudioWavOnly){'1'}else{'0'}
}else{
 Remove-Item Env:SNX_AUDIO_BACKEND,Env:SNX_AUDIO_WAV,Env:SNX_AUDIO_WAV_ONLY -ErrorAction SilentlyContinue
}
if($CaptureTargets){
 $env:SNX_RT_DUMP_DIR=$prefix+'-targets'
 New-Item -ItemType Directory -Force -Path $env:SNX_RT_DUMP_DIR | Out-Null
}else{Remove-Item Env:SNX_RT_DUMP_DIR -ErrorAction SilentlyContinue}
$arguments=@("--game=$game","--seconds=$Seconds",'--log=1','--fullscreen=0',"--docked=$Docked","--shot=$prefix","--press_len=$PressLength","--shot_every=$ShotEvery")
$arguments+='--script='
if($Headless){$arguments+='--headless'}
$runtimeHash=(Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash.ToLowerInvariant()
$codeHash=(Get-FileHash -LiteralPath ($game+'_code.dll') -Algorithm SHA256).Hash.ToLowerInvariant()
$audioHash=if($NativeAudio){(Get-FileHash -LiteralPath $env:SNX_AUDIO_BACKEND -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null}
if($LiveInput){
 $livePath=$prefix+'.inputs.csv'
 Set-Content -LiteralPath $livePath -Value $InputScript -Encoding utf8
 $arguments+="--script_file=$livePath"
 Write-Output "Live diagnostic input: $livePath"
}elseif($InputScript){$arguments+="--script=$InputScript"}
if($CaptureAudioInputs){
 $env:SNX_AUDIO_TRACE_DIR=$prefix+'-audio-inputs'
 New-Item -ItemType Directory -Force -Path $env:SNX_AUDIO_TRACE_DIR | Out-Null
}else{Remove-Item Env:SNX_AUDIO_TRACE_DIR -ErrorAction SilentlyContinue}
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
$audioOutput=if($NativeAudio){$prefix+'.wav'}else{$null}
$result=[ordered]@{mode=$Mode;headless=[bool]$Headless;docked=$Docked;input_script=$InputScript;live_input_file=if($LiveInput){$livePath}else{$null};audio_input_capture=if($CaptureAudioInputs){$env:SNX_AUDIO_TRACE_DIR}else{$null};press_length_ms=$PressLength;shot_every_frames=$ShotEvery;exit_code=$process.ExitCode;elapsed_seconds=[math]::Round($timer.Elapsed.TotalSeconds,2);stdout=$prefix+'.stdout.log';stderr=$prefix+'.stderr.log';game_log=$game+'.log';screenshot=if(Test-Path -LiteralPath ($prefix+'.ppm')){$prefix+'.ppm'}else{$null};playable_validated=$false}
$result['native_audio']=[bool]$NativeAudio
$result['audio_wav']=$audioOutput
$result['audio_wav_only']=[bool]$AudioWavOnly
$result['gpu_fifo_capture']=if($CaptureGpuFifo){$env:SNX_FIFO_TRACE_DIR}else{$null}
$result['graphics_capture_trigger']=if($CaptureGraphics){$env:SNX_RENDERDOC_TRIGGER}else{$null}
$result['runtime_sha256']=$runtimeHash
$result['game_code_sha256']=$codeHash
$result['audio_backend_sha256']=$audioHash
if(Test-Path -LiteralPath ($game+'.log')){
 Copy-Item -LiteralPath ($game+'.log') -Destination ($prefix+'.game.log')
 $result['game_log']=$prefix+'.game.log'
}
if($NativeAudio -and (Test-Path -LiteralPath $audioOutput)){
 & (Join-Path $root 'private/tools/python/python.exe') (Join-Path $root 'scripts/inspect_bridge_audio.py') $audioOutput --finalize
 if($LASTEXITCODE -ne 0){throw 'Audio capture verification failed'}
 $result['audio_analysis']=$prefix+'.audio.json'
}
$result | ConvertTo-Json | Set-Content -LiteralPath ($prefix+'.json') -Encoding utf8
$result | ConvertTo-Json
Select-String -LiteralPath ($prefix+'.stdout.log'),($prefix+'.stderr.log') -Pattern 'RomFS:|vulkan:|FATAL:|Unsupported instruction|svcBreak|frames=' | Select-Object -First 12 | ForEach-Object {$_.Line}
if($process.ExitCode -ne 0){exit $process.ExitCode}
