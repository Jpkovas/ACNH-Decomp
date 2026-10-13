param(
 [ValidateSet('tools','headless','vulkan')][string]$Backend='tools',
 [int]$Jobs=4,
 [string]$Tests='',
 [switch]$GpuTest
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$source=Join-Path $root 'vendor/ScarletNX'
$patch=Join-Path $root 'patches/scarletnx-data-root.patch'
$main=Join-Path $source 'runtime/core/main.c'
if(-not((Get-Content -LiteralPath $main -Raw).Contains('getenv("SNX_DATA_DIR")'))){
 & git -c "safe.directory=$($source.Replace('\','/'))" -C $source apply --check --unidiff-zero $patch
 if($LASTEXITCODE -ne 0){throw 'Pinned runtime data-root patch no longer applies'}
 & git -c "safe.directory=$($source.Replace('\','/'))" -C $source apply --unidiff-zero $patch
 if($LASTEXITCODE -ne 0){throw 'Runtime data-root patch application failed'}
}
$vs='C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools'
$cmake=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ctest=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
$ninja=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$build=Join-Path $root "build/windows-bridge/$Backend"
$temp=Join-Path $root 'private/windows/tmp'
$taskSystemTemp=[IO.Path]::GetTempPath()
New-Item -ItemType Directory -Force -Path $build,$temp | Out-Null
$env:TEMP=$temp
$env:TMP=$temp
if($Backend -eq 'tools'){
 $vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
 $taskEnvironment=& cmd.exe /d /c "call `"$vcvars`" >nul && set"
 if($LASTEXITCODE -ne 0){throw 'MSVC SDK initialization failed'}
 foreach($line in $taskEnvironment){
  if($line -match '^(INCLUDE|LIB|LIBPATH|PATH)=(.*)$'){
   [Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process')
  }
 }
 $llvm=Get-ChildItem -LiteralPath (Join-Path $root 'private/tools/llvm') -Directory | Select-Object -First 1
 $bin=Join-Path $llvm.FullName 'bin'
 $options=@('-DSNX_TOOLS_ONLY=ON')
}else{
 $bin=Join-Path $root 'private/tools/llvm-mingw/llvm-mingw-20261006-ucrt-x86_64/bin'
 if(-not(Test-Path -LiteralPath (Join-Path $bin 'clang.exe'))){throw 'Install the pinned llvm-mingw toolchain first'}
 $options=@('-DSNX_DEPLOY=OFF','-DSNX_H264=OFF',"-DCPM_SOURCE_CACHE=$root/private/tools/cpm-cache")
 if($Backend -eq 'headless'){$options+=@('-DSNX_BACKEND=headless','-DSNX_VULKAN=OFF')}
 else{$options+=@('-DSNX_BACKEND=sdl3','-DSNX_VULKAN=ON')}
 $captureSdk=Join-Path $root 'private/tools/renderdoc/RenderDoc_1.46_64'
 if(Test-Path -LiteralPath (Join-Path $captureSdk 'renderdoc_app.h')){$options+="-DSNX_RENDERDOC_INCLUDE_DIR=$captureSdk"}
 if($GpuTest){$options+='-DSNX_TEST_VULKAN=ON'}
}
$env:PATH="$bin;$(Split-Path $ninja);$env:PATH"
& $cmake -S $source -B $build -G Ninja "-DCMAKE_C_COMPILER=$bin/clang.exe" "-DCMAKE_CXX_COMPILER=$bin/clang++.exe" "-DCMAKE_MAKE_PROGRAM=$ninja" -DCMAKE_BUILD_TYPE=Release -DCMAKE_TRY_COMPILE_CONFIGURATION=Release @options
if($LASTEXITCODE -ne 0){throw 'Windows bridge configuration failed'}
& $cmake --build $build --parallel $Jobs
if($LASTEXITCODE -ne 0){throw 'Windows bridge build failed'}
# Filesystem fixtures verify hard-link semantics, unavailable on the exFAT
# workspace volume. Upstream creates and verifies its own private scratch dir.
$env:TEMP=$taskSystemTemp
$env:TMP=$taskSystemTemp
$testOptions=@()
if($Tests){$testOptions+=@('-R',$Tests)}
& $ctest --test-dir $build --output-on-failure --output-log (Join-Path $build 'test.log') @testOptions
if($LASTEXITCODE -ne 0){throw 'Windows bridge tests failed'}
