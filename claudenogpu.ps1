$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Claude - No GPU.lnk"

$target = "C:\Program Files\WindowsApps\Claude_1.9659.4.0_x64__pzs8sxrjxfjjc\app\claude.exe"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -Command `"& '$target' --disable-gpu`""
$shortcut.WorkingDirectory = Split-Path $target
$shortcut.IconLocation = $target
$shortcut.Save()