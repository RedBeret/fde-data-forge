@echo off
setlocal

echo ============================================================
echo  fde-data-forge — Windows Quick Start
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install Python 3.12+ from https://www.python.org/
    exit /b 1
)

echo [1/2] Installing dependencies...
pip install -r requirements.txt -e . --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    exit /b 1
)

echo [2/2] Verifying installation...
fde --help

echo.
echo ============================================================
echo  fde is installed. Example usage:
echo.
echo    fde detect parts_v1.csv --type parts-v1
echo    fde detect suppliers.csv --type suppliers
echo    fde normalize parts_v1.csv --type parts-v1 --out clean.csv
echo    fde report --parts parts_v1.csv --suppliers suppliers.csv
echo ============================================================

endlocal
