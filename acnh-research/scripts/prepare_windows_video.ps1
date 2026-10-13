$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$lock=Get-Content -LiteralPath (Join-Path $root 'config/tool-nasm.lock.json') -Raw | ConvertFrom-Json
$tools=Join-Path $root 'private/tools/nasm'
$archive=Join-Path $tools $lock.archive
New-Item -ItemType Directory -Force -Path $tools | Out-Null
if(-not(Test-Path -LiteralPath $archive)){
 $partial=$archive+'.part'
 Invoke-WebRequest -Uri $lock.url -OutFile $partial
 if((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $lock.sha256){throw 'NASM download checksum mismatch'}
 Move-Item -LiteralPath $partial -Destination $archive
}
if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $lock.sha256){throw 'NASM archive checksum mismatch'}
$nasm=Join-Path $tools $lock.executable
if(-not(Test-Path -LiteralPath $nasm)){Expand-Archive -LiteralPath $archive -DestinationPath $tools -Force}
if((Get-FileHash -LiteralPath $nasm -Algorithm SHA256).Hash.ToLowerInvariant() -ne $lock.executable_sha256){throw 'NASM executable checksum mismatch'}
$license=Join-Path $tools $lock.license_file
if((Get-FileHash -LiteralPath $license -Algorithm SHA256).Hash.ToLowerInvariant() -ne $lock.license_sha256){throw 'NASM license checksum mismatch'}
$installed=& $nasm -v
if($LASTEXITCODE -ne 0 -or $installed -notmatch ('^NASM version '+[regex]::Escape($lock.version)+' ')){throw 'Unexpected private NASM version'}
Write-Output "Video assembler ready: $installed"
