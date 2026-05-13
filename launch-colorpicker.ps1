$proc = Get-Process PowerToys.ColorPickerUI -ErrorAction SilentlyContinue

if (-not $proc) {
    Start-Process "PowerToys.ColorPickerUI.exe" | Out-Null
    Start-Sleep -Milliseconds 500
}

[System.Threading.EventWaitHandle]::OpenExisting(
    "Local\ShowColorPickerEvent-8c46be2a-3e05-4186-b56b-4ae986ef2525"
).Set() | Out-Null

exit