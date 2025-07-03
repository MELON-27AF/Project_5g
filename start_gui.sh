#!/bin/bash
# Launcher script untuk 5G Emulator GUI
# Linux/Mac Bash Script

echo "==============================================="
echo "          5G Network Emulator GUI"
echo "==============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python tidak ditemukan!"
        echo "Silakan install Python 3.8+ terlebih dahulu."
        echo "Ubuntu/Debian: sudo apt-get install python3"
        echo "CentOS/RHEL: sudo yum install python3"
        echo "macOS: brew install python3"
        exit 1
    else
        PYTHON_CMD=python
    fi
else
    PYTHON_CMD=python3
fi

echo "Python ditemukan: $($PYTHON_CMD --version)"
echo

# Check if tkinter is available
$PYTHON_CMD -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: tkinter tidak tersedia!"
    echo "Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "CentOS/RHEL: sudo yum install tkinter"
    echo "macOS: tkinter biasanya sudah termasuk"
    exit 1
fi

echo "tkinter tersedia."
echo

# Check if GUI script exists
if [ ! -f "5g_emulator_gui.py" ]; then
    echo "ERROR: File 5g_emulator_gui.py tidak ditemukan!"
    echo "Pastikan Anda berada di direktori yang benar."
    exit 1
fi

echo "Starting 5G Emulator GUI..."
echo
echo "Tips:"
echo "- Drag komponen dari panel kiri ke canvas"
echo "- Double-click komponen untuk edit konfigurasi"
echo "- Klik kanan untuk context menu"
echo "- Gunakan Connection Mode untuk menghubungkan komponen"
echo "- Untuk emulasi, pastikan Mininet-WiFi sudah terinstall"
echo

# Start the GUI application
$PYTHON_CMD 5g_emulator_gui.py

if [ $? -ne 0 ]; then
    echo
    echo "Aplikasi berhenti dengan error."
    read -p "Press Enter to continue..."
fi

echo
echo "5G Emulator GUI telah ditutup."
