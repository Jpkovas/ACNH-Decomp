param([ValidateSet('clang','msvc')][string]$Compiler='clang')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$vs='C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools'
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$taskEnvironment=& cmd.exe /d /c "call `"$vcvars`" >nul && set"
if($LASTEXITCODE -ne 0){throw 'MSVC SDK environment initialization failed'}
foreach($line in $taskEnvironment){
 if($line -match '^(INCLUDE|LIB|LIBPATH|PATH)=(.*)$'){[Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process')}
}
$cmake=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ctest=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
$ninja=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$llvm=Get-ChildItem -LiteralPath (Join-Path $root 'private/tools/llvm') -Directory | Select-Object -First 1
$nativeCompiler=if($Compiler -eq 'clang'){Join-Path $llvm.FullName 'bin/clang-cl.exe'}else{(Get-Command cl.exe -ErrorAction Stop).Source}
$build=Join-Path $root ('build/'+$Compiler)
& $cmake -S (Join-Path $root 'reconstructed') -B $build -G Ninja "-DCMAKE_CXX_COMPILER=$nativeCompiler" "-DCMAKE_MAKE_PROGRAM=$ninja" -DCMAKE_BUILD_TYPE=Release -DCMAKE_TRY_COMPILE_CONFIGURATION=Release
if($LASTEXITCODE -ne 0){throw "$Compiler CMake configuration failed"}
& $cmake --build $build
if($LASTEXITCODE -ne 0){throw "$Compiler build failed"}
& $ctest --test-dir $build --output-on-failure --output-log (Join-Path $build 'test.log')
if($LASTEXITCODE -ne 0){throw "$Compiler tests failed"}
