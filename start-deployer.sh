#!/bin/bash
cd "$(dirname "$0")"

echo "=============================================="
echo "  Universal App Deployer Launcher for macOS/Linux"
echo "=============================================="
echo ""

echo "[*] Checking for Python3..."
if ! command -v python3 &> /dev/null; then
    echo "[!] Python3 not found."
    
    if [ "$(uname)" == "Darwin" ]; then
        echo "[*] Automatically downloading Python 3 for macOS..."
        curl -L -o /tmp/python_installer.pkg "https://www.python.org/ftp/python/3.11.8/python-3.11.8-macos11.pkg"
        echo "[*] Installing Python (this requires your Mac password)..."
        sudo installer -pkg /tmp/python_installer.pkg -target /
    else
        echo "[*] Attempting to install Python3 via apt-get (Linux)..."
        sudo apt-get update && sudo apt-get install -y python3 python3-tk
    fi
else
    echo "[OK] Python3 is installed."
fi

# Check for tkinter (GUI library) which is sometimes stripped out on macOS default python
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "[!] Tkinter (GUI library) is missing from your Python installation."
    if [ "$(uname)" == "Darwin" ]; then
        echo "[*] Downloading official Mac Python installer to fix GUI support..."
        curl -L -o /tmp/python_installer.pkg "https://www.python.org/ftp/python/3.11.8/python-3.11.8-macos11.pkg"
        echo "[*] Installing... (requires Mac password)"
        sudo installer -pkg /tmp/python_installer.pkg -target /
    fi
fi

echo ""
echo "[*] Launching Universal App Deployer..."
python3 Universal-App-Deployer.py
