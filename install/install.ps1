$ErrorActionPreference = "Stop"

$repo = if ($env:HACKLUMINARY_REPO) { $env:HACKLUMINARY_REPO } else { "MindCore/HackLuminary" }
$version = if ($env:HACKLUMINARY_VERSION) { $env:HACKLUMINARY_VERSION } else { "latest" }
$installDir = if ($env:HACKLUMINARY_INSTALL_DIR) { $env:HACKLUMINARY_INSTALL_DIR } else { "$HOME\AppData\Local\Programs\HackLuminary" }

$asset = "hackluminary-windows-x64.zip"
if ($version -eq "latest") {
    $url = "https://github.com/$repo/releases/latest/download/$asset"
} else {
    if (-not $version.StartsWith("v")) { $version = "v$version" }
    $url = "https://github.com/$repo/releases/download/$version/$asset"
}

$tmpDir = Join-Path $env:TEMP ("hackluminary-install-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmpDir | Out-Null

try {
    $zipPath = Join-Path $tmpDir $asset
    Write-Host "Downloading $url"
    Invoke-WebRequest -Uri $url -OutFile $zipPath

    Expand-Archive -Path $zipPath -DestinationPath $tmpDir -Force
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Copy-Item -Path (Join-Path $tmpDir "hackluminary.exe") -Destination (Join-Path $installDir "hackluminary.exe") -Force

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
        Write-Host "Added $installDir to user PATH. Restart terminal to use hackluminary."
    }

    Write-Host "Installed hackluminary.exe to $installDir"
    Write-Host "Run: hackluminary --help"
}
finally {
    Remove-Item -Path $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

