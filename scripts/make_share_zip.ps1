# Build a share zip that omits private proofs and runtime debris.
param(
  [string]$OutZip = ""
)
$Root = Split-Path -Parent $PSScriptRoot
if (-not $OutZip) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $OutZip = Join-Path (Split-Path $Root) "agency-harness-$stamp.zip"
}
$stage = Join-Path $env:TEMP ("ah-universal-stage-" + [guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Force -Path $stage | Out-Null
try {
  robocopy $Root $stage /E /NFL /NDL /NJH /NJS /XD docs\private tmp .git .venv venv __pycache__ /XF models.yaml .env | Out-Null
  if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
  Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $OutZip -Force
  Write-Host "Wrote $OutZip"
} finally {
  Remove-Item $stage -Recurse -Force -EA SilentlyContinue
}
