param([string]$Root = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference = 'Stop'
$repos = [ordered]@{
  'CylindricalEarth' = 'Treeki/CylindricalEarth'
  'acnh-eventflow-decompiler' = 'asteriation/acnh-eventflow-decompiler'
  'acnh-eventflow-compiler' = 'asteriation/acnh-eventflow-compiler'
  'Ghidra-Switch-Loader' = 'Adubbz/Ghidra-Switch-Loader'
  'evfl' = 'zeldamods/evfl'
  'sarc' = 'zeldamods/sarc'
  'objdiff' = 'encounter/objdiff'
  'ac-decomp' = 'ACreTeam/ac-decomp'
  'Switch-Toolbox' = 'KillzXGaming/Switch-Toolbox'
  'decompedia' = 'decompals/decompedia'
  'dtk-template' = 'encounter/dtk-template'
  'hactool' = 'SciresM/hactool'
  'hactool-modern' = 'borntohonk/hactool'
}
$vendor = Join-Path $Root 'vendor'
New-Item -ItemType Directory -Path $vendor -Force | Out-Null
$locked = @()
$lockFile=Join-Path $Root 'config/sources.lock.json'
$prior=@{}
if(Test-Path -LiteralPath $lockFile){foreach($item in (Get-Content -LiteralPath $lockFile -Raw | ConvertFrom-Json).sources){$prior[$item.name]=$item}}
foreach ($name in $repos.Keys) {
  $destination = Join-Path $vendor $name
  $url = 'https://github.com/' + $repos[$name] + '.git'
  if (-not (Test-Path -LiteralPath $destination)) {
    & git -c core.longpaths=true clone --depth 1 --no-checkout $url $destination
    if ($LASTEXITCODE -ne 0) { throw "Clone failed: $name" }
    if($prior.ContainsKey($name)){
      & git -C $destination fetch --depth 1 origin $prior[$name].commit
      if($LASTEXITCODE -ne 0){throw "Pinned revision fetch failed: $name"}
      & git -C $destination checkout --detach $prior[$name].commit
    }else{& git -C $destination checkout --detach HEAD}
    if($LASTEXITCODE -ne 0){throw "Pinned checkout failed: $name"}
  }
  $commit = (& git -c "safe.directory=$destination" -C $destination rev-parse HEAD).Trim()
  if ($LASTEXITCODE -ne 0) { throw "Commit missing: $name" }
  if($prior.ContainsKey($name) -and $commit -ne $prior[$name].commit){throw "Existing checkout differs from source lock: $name"}
  $licenses = @(Get-ChildItem -LiteralPath $destination -File | Where-Object { $_.Name -match '^(LICENSE|COPYING|COPYRIGHT)' } | ForEach-Object { @{path=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
  $locked += @{name=$name;url=$url;commit=$commit;licenses=$licenses}
  @{schema_version=1;sources=$locked} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Root 'config/sources.lock.json') -Encoding utf8
  Write-Output "$name pinned at $commit"
}
