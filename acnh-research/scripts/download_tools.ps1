param([ValidateSet('ghidra','jdk','objdiff','llvm','hactoolmodern')][string]$Tool)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$downloads=Join-Path $root 'private/tools/downloads'
New-Item -ItemType Directory -Path $downloads -Force | Out-Null
$sources=@{
 hactoolmodern=@{repo='borntohonk/hactool';tag='1.5.4';pattern='^hactool-windows\.zip$'}
 ghidra=@{repo='NationalSecurityAgency/ghidra';tag='Ghidra_12.1.4_build';pattern='^ghidra_12\.1\.4_PUBLIC_.*\.zip$'}
 jdk=@{repo='adoptium/temurin21-binaries';tag='jdk-21.0.12.1+1';pattern='^OpenJDK21U-jdk_x64_windows_hotspot_.*\.zip$'}
 objdiff=@{repo='encounter/objdiff';tag='v3.8.2';pattern='^objdiff-cli-windows-x86_64\.exe$'}
 llvm=@{repo='llvm/llvm-project';tag='llvmorg-23.1.3';pattern='^clang\+llvm-23\.1\.3-x86_64-pc-windows-msvc\.tar\.zst$'}
}
$source=$sources[$Tool]
$release=Invoke-RestMethod -Uri ('https://api.github.com/repos/'+$source.repo+'/releases/tags/'+[Uri]::EscapeDataString($source.tag)) -Headers @{'User-Agent'='ACNH-local-research'}
$asset=@($release.assets | Where-Object { $_.name -match $source.pattern })
if ($asset.Count -ne 1) { throw 'Expected exactly one release asset' }
$asset=$asset[0]
$file=Join-Path $downloads $asset.name
if (-not (Test-Path -LiteralPath $file)) {
 & curl.exe --fail --location --retry 3 --silent --show-error --output $file $asset.browser_download_url
 if ($LASTEXITCODE -ne 0) { throw 'Download failed' }
}
if ((Get-Item -LiteralPath $file).Length -ne $asset.size) { throw 'Release asset size mismatch' }
$hash=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
if ($asset.digest -and $asset.digest -ne ('sha256:'+$hash)) { throw 'Release SHA-256 mismatch' }
$priorLock=Join-Path $root ('config/tool-'+$Tool+'.lock.json')
if(Test-Path -LiteralPath $priorLock){
 $prior=Get-Content -LiteralPath $priorLock -Raw | ConvertFrom-Json
 if($prior.sha256 -ne $hash){throw 'Distribution differs from pinned local SHA-256'}
}
$lock=@{tool=$Tool;tag=$source.tag;url=$asset.browser_download_url;size=$asset.size;sha256=$hash;upstream_digest_verified=[bool]$asset.digest}
$lock | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root ('config/tool-'+$Tool+'.lock.json')) -Encoding utf8
if ($file.EndsWith('.zip')) {
 Expand-Archive -LiteralPath $file -DestinationPath (Join-Path $root ('private/tools/'+$Tool)) -Force
}
Write-Output ($Tool+' ready; SHA-256 '+$hash)
