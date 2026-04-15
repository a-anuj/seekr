#!/bin/bash

# 1. Get the absolute path of the current directory
INSTALL_DIR=$(pwd)
ICON_PATH="$INSTALL_DIR/assets/logo.png" # Make sure your logo is here!
SCRIPT_PATH="$INSTALL_DIR/app/main_gtk.py"

echo "🚀 Installing Seekr..."

# 2. Install Python Dependencies
echo "📦 Installing dependencies..."
pip install keyring rapidocr-onnxruntime gi-docgen --user

# 3. Create the Desktop Entry dynamically
echo "📝 Creating desktop entry..."
mkdir -p ~/.local/share/applications

cat <<EOF > ~/.local/share/applications/com.seekr.app.desktop
[Desktop Entry]
Name=Seekr
Comment=AI-Powered File Search
# 🚀 THE FIX: Run python with the project root in the path
Exec=env PYTHONPATH=$INSTALL_DIR /usr/bin/python3 $SCRIPT_PATH
Path=$INSTALL_DIR
Icon=$ICON_PATH
Type=Application
Categories=Utility;System;
Terminal=false
StartupNotify=true
EOF

# 4. Finalize Permissions
echo "🔐 Setting permissions..."
chmod +x ~/.local/share/applications/com.seekr.app.desktop
chmod +x "$SCRIPT_PATH"

# 5. Update Desktop Database
update-desktop-database ~/.local/share/applications/

echo "✅ Done! You can now find 'Seekr' in your Application Menu."