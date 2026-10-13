$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$cmakeDir='C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake'
$cmake=Join-Path $cmakeDir 'CMake/bin/cmake.exe'
$ninja=Join-Path $cmakeDir 'Ninja/ninja.exe'
$bin=Join-Path $root 'private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin'
$build=Join-Path $root 'build/windows-video-fixture'
$logs=Join-Path $root 'private/windows/video-fixture'
$env:PATH="$bin;$env:PATH"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
& $cmake -S (Join-Path $root 'windows_video') -B $build -G Ninja "-DCMAKE_C_COMPILER=$bin/clang.exe" "-DCMAKE_MAKE_PROGRAM=$ninja" -DCMAKE_BUILD_TYPE=Release
if($LASTEXITCODE -ne 0){throw 'Video fixture configuration failed'}
& $cmake --build $build --parallel 4
if($LASTEXITCODE -ne 0){throw 'Video fixture build failed'}
$exe=Join-Path $build 'acnh-video-fixture.exe'
$output=& $exe 2> (Join-Path $logs 'stderr.log')
if($LASTEXITCODE -ne 0){throw 'Native NVDEC/VIC fixture failed'}
$output | Set-Content -LiteralPath (Join-Path $logs 'result.json') -Encoding utf8
$result=$output | ConvertFrom-Json
if($result.failures -ne 0 -or $result.cases -ne 11 -or $result.h264_frames -ne 3 -or $result.guest_cpu){throw 'Unexpected video fixture evidence'}
Write-Output "Native NVDEC/VIC: $($result.cases) cases passed (3 independent H.264 frames, 6 exact RGBA/BGRA outputs, 2 failure statuses)"
