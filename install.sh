#!/bin/bash

set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_PATH="$INSTALL_DIR/assets/logo.png"
SCRIPT_PATH="$INSTALL_DIR/app/main_gtk.py"

echo "🚀 Installing Seekr..."

# -------------------------------
# 1. Check system dependencies
# -------------------------------
echo "🔍 Checking GTK (gi) dependency..."

if ! python3 -c "import gi" 2>/dev/null; then
  echo "❌ PyGObject (gi) not found. Installing..."

  if command -v dnf &> /dev/null; then
    sudo dnf install -y python3-gobject gtk4
  elif command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3-gi gir1.2-gtk-4.0
  else
    echo "⚠️ Unsupported package manager. Install GTK manually."
    exit 1
  fi
fi

# -------------------------------
# 2. Install Python dependencies
# -------------------------------
echo "📦 Installing Python dependencies..."

python3 -m pip install --user --upgrade pip
python3 -m pip install --user keyring rapidocr-onnxruntime gi-docgen

# -------------------------------
# 3. Validate files
# -------------------------------
echo "📁 Validating project files..."

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "❌ main_gtk.py not found!"
  exit 1
fi

if [ ! -f "$ICON_PATH" ]; then
  echo "⚠️ Icon not found, continuing without icon..."
  ICON_LINE="# Icon not set"
else
  ICON_LINE="Icon=$ICON_PATH"
fi

# -------------------------------
# 4. Create desktop entry
# -------------------------------
echo "📝 Creating desktop entry..."

mkdir -p ~/.local/share/applications

cat <<EOF > ~/.local/share/applications/com.seekr.app.desktop
[Desktop Entry]
Name=Seekr
Comment=AI-Powered File Search
Exec=bash -c "cd $INSTALL_DIR && PYTHONPATH=$INSTALL_DIR python3 $SCRIPT_PATH 2>>/tmp/seekr-error.log"
Path=$INSTALL_DIR
$ICON_LINE
Type=Application
Categories=Utility;System;
Terminal=false
StartupNotify=true
EOF

# -------------------------------
# 5. Permissions
# -------------------------------
echo "🔐 Setting permissions..."

chmod +x ~/.local/share/applications/com.seekr.app.desktop
chmod +x "$SCRIPT_PATH"

# -------------------------------
# 6. Refresh system
# -------------------------------
echo "🔄 Updating application database..."

update-desktop-database ~/.local/share/applications 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo "👉 Search 'Seekr' in app menu"
echo "🐞 Logs: /tmp/seekr-error.log"