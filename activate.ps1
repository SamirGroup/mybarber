# Terminalda bir marta ishga tushiring:  . .\activate.ps1
$Root = $PSScriptRoot
Set-Location $Root
& "$Root\.venv\Scripts\Activate.ps1"
Write-Host "Virtual muhit yoqildi. Endi: python manage.py migrate"
