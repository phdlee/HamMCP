# Download official Hamlib Windows x64 binaries into vendor/ (for maintainers).
$ErrorActionPreference = "Stop"
$Version = "4.7.2"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Vendor = Join-Path $Root "hamlib-mcp\vendor"
$ZipName = "hamlib-w64-$Version.zip"
$Url = "https://github.com/Hamlib/Hamlib/releases/download/$Version/$ZipName"
$ZipPath = Join-Path $env:TEMP $ZipName
$Dest = Join-Path $Vendor "hamlib-w64-$Version"

New-Item -ItemType Directory -Force -Path $Vendor | Out-Null
Write-Host "Downloading $Url ..."
Invoke-WebRequest -Uri $Url -OutFile $ZipPath -UseBasicParsing
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
Expand-Archive -Path $ZipPath -DestinationPath $Dest -Force
Remove-Item $ZipPath -Force
$rigctl = Get-ChildItem -Path $Dest -Recurse -Filter "rigctl.exe" | Select-Object -First 1
if (-not $rigctl) { throw "rigctl.exe not found after extract" }
Write-Host "OK: $($rigctl.FullName)"
