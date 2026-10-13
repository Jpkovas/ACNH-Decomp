param([switch]$ManagedOnly)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$dotnet=Join-Path $root 'private/tools/dotnet-8.0.425/dotnet.exe'
$source=Join-Path $root 'vendor/ryujinx-audio-reference'
if(-not(Test-Path -LiteralPath $dotnet)){throw 'Install the SDK recorded in config/tool-dotnet.lock.json'}
$revision=& git -c "safe.directory=$($source.Replace('\','/'))" -C $source rev-parse HEAD
if($revision -ne 'fec4f4ada9f28f897457033f9954c84cc15d0b02'){throw 'Unexpected audio reference revision'}
$env:DOTNET_CLI_HOME=Join-Path $root 'private/tools/dotnet-home'
$env:NUGET_PACKAGES=Join-Path $root 'private/tools/nuget-packages'
$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
$env:DOTNET_NOLOGO='1'
$argsList=@((Join-Path $root 'windows_audio/AcnhAudio.csproj'),'-c','Release','-r','win-x64',"-p:RestorePackagesPath=$env:NUGET_PACKAGES",'-v','minimal')
if($ManagedOnly){& $dotnet build @argsList}
else{
 $vcvars='C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
 $environment=& cmd.exe /d /c "call `"$vcvars`" >nul && set"
 if($LASTEXITCODE -ne 0){throw 'MSVC SDK initialization failed'}
 foreach($line in $environment){
  if($line -match '^(INCLUDE|LIB|LIBPATH|PATH)=(.*)$'){
   [Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process')
  }
 }
 & $dotnet publish @argsList -o (Join-Path $root 'private/windows/audio')
}
if($LASTEXITCODE -ne 0){throw 'Windows audio build failed'}
