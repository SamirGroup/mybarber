# Maktab ERP — virtual muhit bilan ishga tushirish
$Root = $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual muhit yaratilmoqda..."
    py -3 -m venv .venv
    .\.venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host "Server: http://127.0.0.1:8000/"
.\.venv\Scripts\python.exe manage.py runserver
