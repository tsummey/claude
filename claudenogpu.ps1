# Relaunch as admin if not already elevated
$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)

if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe `
        -Verb RunAs `
        -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Claude - No GPU.lnk"

$target = Get-ChildItem "C:\Program Files\WindowsApps" -Directory -Filter "Claude_*" |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object { Join-Path $_.FullName "app\claude.exe" } |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $target) {
    throw "Claude executable not found. WindowsApps has once again chosen violence."
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -Command `"& '$target' --disable-gpu`""
$shortcut.WorkingDirectory = Split-Path $target
$shortcut.IconLocation = $target
$shortcut.Save()