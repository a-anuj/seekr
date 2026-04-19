#!/bin/bash

set -e

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_PATH="$INSTALL_DIR/assets/logo.png"
SCRIPT_PATH="$INSTALL_DIR/app_entry/main_gtk.py"

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
  elif command -v pacman &> /dev/null; then
    sudo pacman -Sy --noconfirm python-gobject gtk4
  elif command -v zypper &> /dev/null; then
    sudo zypper install -y python3-gobject gtk4
  elif command -v apk &> /dev/null; then
    sudo apk add py3-gobject3 gtk4.0
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

# -------------------------------
# 4. Create CLI shortcut
# -------------------------------
echo "📝 Creating CLI shortcut..."

mkdir -p ~/.local/bin

cat <<EOF > ~/.local/bin/seekr
#!/bin/bash
export PYTHONPATH="$INSTALL_DIR"
cd "$INSTALL_DIR" || exit 1
python3 "$SCRIPT_PATH" "\\\$@"
EOF

# -------------------------------
# 5. Permissions
# -------------------------------
echo "🔐 Setting permissions..."

chmod +x ~/.local/bin/seekr
chmod +x "$SCRIPT_PATH"

echo ""
echo "✅ Installation complete!"
echo "👉 You can now run Seekr by typing 'seekr' in your terminal."
echo "⚠️  Note: Make sure ~/.local/bin is in your PATH."
echo "🐞 Logs: /tmp/seekr-error.log"