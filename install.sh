#!/bin/bash
# Install script for Sequel Ace Backup Tool

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Sequel Ace Backup Tool - Installer"
echo "===================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Determine install location
INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="sequel-ace-backup"
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/sequel_ace_backup.py"

# Check if we can write to /usr/local/bin
if [ ! -w "$INSTALL_DIR" ]; then
    echo ""
    echo -e "${YELLOW}Note:${NC} Installing to $INSTALL_DIR requires sudo access"
    echo "You'll be prompted for your password."
    echo ""

    # Create symlink with sudo
    sudo ln -sf "$SCRIPT_PATH" "$INSTALL_DIR/$SCRIPT_NAME"
else
    # Create symlink without sudo
    ln -sf "$SCRIPT_PATH" "$INSTALL_DIR/$SCRIPT_NAME"
fi

# Make the script executable
chmod +x "$SCRIPT_PATH"

echo ""
echo -e "${GREEN}✓${NC} Installation complete!"
echo ""
echo "You can now use the tool from anywhere by typing:"
echo "  $SCRIPT_NAME backup"
echo "  $SCRIPT_NAME restore -f backup_file.json"
echo "  $SCRIPT_NAME list -f backup_file.json"
echo ""
echo "Run '$SCRIPT_NAME --help' for more information."
