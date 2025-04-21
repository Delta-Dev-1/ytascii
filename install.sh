#!/bin/bash

set -e

INSTALL_PATH="/usr/local/bin"
SCRIPT_NAME="ytascii"

usage() {
    echo "Usage:"
    echo "  ./install.sh        Install ytascii"
    echo "  ./install.sh -u     Uninstall ytascii"
    exit 1
}

if [ "$1" == "-u" ]; then
    echo "🧹 Uninstalling ytascii..."
    if [ -f "$INSTALL_PATH/$SCRIPT_NAME" ]; then
        sudo rm "$INSTALL_PATH/$SCRIPT_NAME"
        echo "✅ Removed $INSTALL_PATH/$SCRIPT_NAME"
    else
        echo "⚠️  ytascii is not installed in $INSTALL_PATH"
    fi
    exit 0
elif [ -n "$1" ]; then
    usage
fi

echo "📦 Installing ytascii..."

if [ ! -f "./$SCRIPT_NAME.py" ]; then
    echo "❌ Error: $SCRIPT_NAME.py not found in the current directory."
    exit 1
fi

chmod +x "$SCRIPT_NAME.py"
sudo cp "$SCRIPT_NAME.py" "$INSTALL_PATH/$SCRIPT_NAME"

echo "✅ ytascii installed to $INSTALL_PATH/$SCRIPT_NAME"
echo "💡 You can now run it with: $SCRIPT_NAME \"<YouTube URL>\""
