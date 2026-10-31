# Copy portable skills into Kilo skills dir (default: %USERPROFILE%\.kilocode\skills)
$ErrorActionPreference = 'Stop'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $Root 'skills\agency-advance\SKILL.md'))) {
  $Root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
}
$DestRoot = Join-Path $env:USERPROFILE '.kilocode\skills'
# Fallbacks
if (-not (Test-Path (Split-Path $DestRoot))) {
  $alt = Join-Path $env:USERPROFILE '.kilo\skills'
  $DestRoot = $alt
}
New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
foreach ($name in @('agency-advance','agency-replay')) {
  $src = Join-Path $Root "skills\$name"
  $dst = Join-Path $DestRoot $name
  if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
  Copy-Item -Recurse $src $dst
  Write-Host "Installed $dst"
}
Write-Host "Done. If Kilo uses a different skills path, move these folders there."
