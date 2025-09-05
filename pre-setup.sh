#!/bin/bash
set -e

echo "🔧 Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pyqt5

echo "📂 Creating Odin4GUIFiles directory in root..."
sudo mkdir -p /Odin4GUIFiles

echo "📦 Moving odin4gui.py into /Odin4GUIFiles..."
sudo cp "$(dirname "$0")/odin4gui.py" /Odin4GUIFiles/

echo "⚡ Installing odin4 executable into /usr/local/bin..."
sudo cp "$(dirname "$0")/odin4" /usr/local/bin/
sudo chmod +x /usr/local/bin/odin4

echo "✅ Pre-setup finished!"
