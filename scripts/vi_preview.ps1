param(
  [Parameter(Mandatory = $false)]
  [string]$Url = "",
  [switch]$DoctorOnly
)
$ErrorActionPreference = "Stop"

# Portable VI preview helper for Agency Harness Universal.
# Requires browser-use helpers under %USERPROFILE%\.local\bin (bu-chrome / bu-doctor / browser-use).
# Never binds 0.0.0.0. Never tunnels CDP. Never attaches to the operator daily browser profile.

$BuChrome = Join-Path $env:USERPROFILE ".local\bin\bu-chrome.cmd"
$BuDoctor = Join-Path $env:USERPROFILE ".local\bin\bu-doctor.cmd"
$BuEnv = Join-Path $env:USERPROFILE ".local\bin\bu-env.ps1"
$BrowserUse = Join-Path $env:USERPROFILE ".local\bin\browser-use.exe"

function Ensure-IsolatedCdp {
  if (Test-Path $BuEnv) {
    . $BuEnv
  } else {
    $env:BU_CDP_URL = "http://127.0.0.1:9222"
  }
  if (-not $env:BU_CDP_URL) {
    $env:BU_CDP_URL = "http://127.0.0.1:9222"
  }
  if ($env:BU_CDP_URL -notmatch "^https?://127\.0\.0\.1(:\d+)?(/.*)?$") {
    throw "Refusing non-localhost BU_CDP_URL: $($env:BU_CDP_URL)"
  }
  if (Test-Path $BuDoctor) {
    & $BuDoctor
    if ($LASTEXITCODE -ne 0) {
      throw "bu-doctor failed (exit $LASTEXITCODE). Start isolated Chrome first: $BuChrome"
    }
  } elseif (Test-Path $BuChrome) {
    & $BuChrome
    Start-Sleep -Seconds 2
  } else {
    throw "Missing bu-doctor.cmd / bu-chrome.cmd under ~/.local/bin - see docs/vi-preview-browser-use.md"
  }
}

Ensure-IsolatedCdp
Write-Host "BU_CDP_URL=$($env:BU_CDP_URL)"

if ($DoctorOnly -or -not $Url) {
  if (Test-Path $BrowserUse) {
    "print(page_info())" | & $BrowserUse
  }
  Write-Host "Doctor/CDP path ready. Pass -Url to open a preview tab."
  exit 0
}

if ($Url -notmatch "^(https?|file):") {
  throw "Url must start with http://, https://, or file:"
}

if (-not (Test-Path $BrowserUse)) {
  throw "browser-use.exe not found at $BrowserUse"
}

$py = @"
ensure_real_tab()
new_tab("$Url")
print(page_info())
"@
$py | & $BrowserUse
if ($LASTEXITCODE -ne 0) {
  throw "browser-use navigation failed (exit $LASTEXITCODE)"
}
Write-Host "Opened preview in isolated profile: $Url"
Write-Host "Visual-inspector: capture screenshots/a11y from this tab. Do not merge. Do not use the operator daily browser."