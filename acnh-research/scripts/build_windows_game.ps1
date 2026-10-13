param([ValidateRange(1,16)][int]$Jobs=8)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python=Join-Path $root 'private/tools/python/python.exe'
& $python (Join-Path $root 'scripts/replace_bridge_routines.py')
if($LASTEXITCODE -ne 0){throw 'Reviewed source replacement failed'}
$vs='C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools'
$cmake=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ninja=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$bin=Join-Path $root 'private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin'
$env:PATH="$bin;$env:PATH"
$build=Join-Path $root 'build/windows-bridge/game-o1'
$game=Join-Path $root 'private/windows/bridge'
& $cmake -S (Join-Path $root 'windows_bridge') -B $build -G Ninja "-DCMAKE_C_COMPILER=$bin/clang.exe" "-DCMAKE_CXX_COMPILER=$bin/clang++.exe" "-DCMAKE_MAKE_PROGRAM=$ninja" "-DGENERATED_DIR=$game/ACNH_1_0_0_build" "-DSCARLET_DIR=$root/vendor/ScarletNX" "-DGAME_OUTPUT=$game" -DCMAKE_BUILD_TYPE=Release
if($LASTEXITCODE -ne 0){throw 'ACNH module configuration failed'}
& $cmake --build $build --parallel $Jobs
if($LASTEXITCODE -ne 0){throw 'ACNH module build failed'}
Copy-Item -LiteralPath (Join-Path $root 'build/windows-bridge/vulkan/scarletnx.exe') -Destination (Join-Path $game 'ACNH_1_0_0.exe')
