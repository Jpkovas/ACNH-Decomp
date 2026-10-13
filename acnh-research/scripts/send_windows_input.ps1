param(
 [Parameter(Mandatory=$true)][string]$LiveFile,
 [Parameter(Mandatory=$true)][string[]]$Buttons,
 [ValidateRange(1,60)][int]$AfterSeconds=5,
 [ValidateRange(1,60)][int]$IntervalSeconds=8,
 [ValidateRange(1,10000)][int]$HoldMilliseconds=300
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$path=[IO.Path]::GetFullPath($LiveFile)
$logs=[IO.Path]::GetFullPath((Join-Path $root 'private/windows/logs'))+[IO.Path]::DirectorySeparatorChar
if(-not $path.StartsWith($logs,[StringComparison]::OrdinalIgnoreCase) -or -not $path.EndsWith('.inputs.csv')){throw 'Use the task-owned private live input file'}
$prefix=[IO.Path]::GetFileName($path).Replace('.inputs.csv','')
$runtime=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'scarletnx.exe' -and $_.CommandLine.Contains($prefix)})
if($runtime.Count -ne 1){throw 'Expected exactly one matching runtime'}
$elapsed=[int64](((Get-Date)-$runtime[0].CreationDate).TotalMilliseconds)
$events=for($i=0;$i -lt $Buttons.Count;$i++){
 if($Buttons[$i] -notmatch '^[0-9a-fA-F]+$'){throw 'Buttons must be hexadecimal masks'}
 "$($elapsed+($AfterSeconds+$IntervalSeconds*$i)*1000):$($Buttons[$i]):$HoldMilliseconds"
}
$budgetMatch=[regex]::Match($runtime[0].CommandLine,'--seconds=(\d+)')
if(-not $budgetMatch.Success){throw 'Runtime has no diagnostic deadline'}
$deadline=[int64]$budgetMatch.Groups[1].Value*1000
$last=$elapsed+($AfterSeconds+$IntervalSeconds*($Buttons.Count-1))*1000+$HoldMilliseconds
if($last -ge $deadline){throw 'Scheduled controls would exceed this run deadline; wait for a new run'}
$script=$events -join ','
Set-Content -LiteralPath $path -Value $script -Encoding utf8
$record=[ordered]@{pid=$runtime[0].ProcessId;elapsed_ms=$elapsed;script=$script;method='script_file reload; per-press duration';deadline_ms=$deadline}
$record | ConvertTo-Json | Set-Content -LiteralPath ($path.Replace('.inputs.csv','-input-'+(Get-Date -Format 'HHmmss')+'.json')) -Encoding utf8
$record | ConvertTo-Json
