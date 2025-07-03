@echo off
REM Launcher script untuk 5G Emulator GUI
REM Windows Batch Script

echo ===============================================
echo          5G Network Emulator GUI
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan!
    echo Silakan install Python 3.8+ terlebih dahulu.
    echo Download dari: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python ditemukan.
echo.

REM Check if tkinter is available
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ERROR: tkinter tidak tersedia!
    echo Silakan install tkinter atau gunakan Python yang sudah include tkinter.
    pause
    exit /b 1
)

echo tkinter tersedia.
echo.

REM Check if GUI script exists
if not exist "5g_emulator_gui.py" (
    echo ERROR: File 5g_emulator_gui.py tidak ditemukan!
    echo Pastikan Anda berada di direktori yang benar.
    pause
    exit /b 1
)

echo Starting 5G Emulator GUI...
echo.
echo Tips:
echo - Drag komponen dari panel kiri ke canvas
echo - Double-click komponen untuk edit konfigurasi
echo - Klik kanan untuk context menu
echo - Gunakan Connection Mode untuk menghubungkan komponen
echo.

REM Start the GUI application
python 5g_emulator_gui.py

if errorlevel 1 (
    echo.
    echo Aplikasi berhenti dengan error.
    pause
)

echo.
echo 5G Emulator GUI telah ditutup.
pause
