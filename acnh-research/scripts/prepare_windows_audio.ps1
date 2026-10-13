$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$lock=Get-Content -LiteralPath (Join-Path $root 'config/tool-dotnet.lock.json') -Raw | ConvertFrom-Json
$tools=Join-Path $root 'private/tools'
$sdk=Join-Path $tools ('dotnet-'+$lock.version)
if(-not(Test-Path -LiteralPath (Join-Path $sdk 'dotnet.exe'))){
 $archive=Join-Path $tools ('dotnet-sdk-'+$lock.version+'-win-x64.zip')
 New-Item -ItemType Directory -Force -Path $tools | Out-Null
 if(-not(Test-Path -LiteralPath $archive)){Invoke-WebRequest -Uri $lock.url -OutFile $archive}
 if((Get-FileHash -LiteralPath $archive -Algorithm SHA512).Hash.ToLowerInvariant() -ne $lock.sha512){throw 'SDK archive checksum mismatch'}
 Expand-Archive -LiteralPath $archive -DestinationPath $sdk -Force
}
$installed=& (Join-Path $sdk 'dotnet.exe') --version
if($installed -ne $lock.version){throw 'Unexpected private SDK version'}
$repo=Join-Path $root 'vendor/ryujinx-audio-reference'
$source=(Get-Content -LiteralPath (Join-Path $root 'config/windows-sources.lock.json') -Raw | ConvertFrom-Json).sources | Where-Object name -eq 'Ryujinx.Audio'
if(-not $source){throw 'Missing audio source lock'}
$gitPath=$repo.Replace('\','/')
if(-not(Test-Path -LiteralPath $repo)){
 & git -c core.longpaths=true clone --filter=blob:none --no-checkout $source.url $repo
 if($LASTEXITCODE -ne 0){throw 'Audio reference clone failed'}
 & git -c "safe.directory=$gitPath" -C $repo fetch --depth 1 origin $source.commit
 if($LASTEXITCODE -ne 0){throw 'Pinned audio revision fetch failed'}
 & git -c "safe.directory=$gitPath" -C $repo sparse-checkout set src/Ryujinx.Audio src/Ryujinx.Common src/Ryujinx.Memory
 if($LASTEXITCODE -ne 0){throw 'Audio sparse checkout failed'}
 & git -c "safe.directory=$gitPath" -C $repo checkout --detach $source.commit
 if($LASTEXITCODE -ne 0){throw 'Pinned audio checkout failed'}
}
$actual=& git -c "safe.directory=$gitPath" -C $repo rev-parse HEAD
if($actual -ne $source.commit){throw 'Existing audio checkout differs from the source lock'}
foreach($license in $source.licenses){
 if((Get-FileHash -LiteralPath (Join-Path $repo $license.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $license.sha256){throw 'Audio license checksum mismatch'}
}
Write-Output "Audio reference ready at $actual; private .NET SDK $installed"
