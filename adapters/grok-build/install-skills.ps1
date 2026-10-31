$ErrorActionPreference = 'Stop'
$Root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$DestRoot = Join-Path $Root '.grok\skills'
New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
foreach ($name in @('agency-advance','agency-replay')) {
  $src = Join-Path $Root "skills\$name"
  $dst = Join-Path $DestRoot $name
  if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
  Copy-Item -Recurse $src $dst
  Write-Host "Installed $dst"
}
