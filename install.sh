#!/usr/bin/env bash
# macOS / Linux Installer for ga4-ai-bridge
set -e

echo "=========================================="
echo "  Installing ga4-ai-bridge (Unix)         "
echo "=========================================="

PYTHON_CMD=$(which python3 || which python || true)
if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi
echo "[+] Found Python: $PYTHON_CMD"

echo "[*] Installing Python dependencies..."
$PYTHON_CMD -m pip install -r "$(dirname "$0")/requirements.txt" --quiet
echo "[+] Dependencies installed successfully."

GA4_HOME="$HOME/.ga4"
GA4_BIN="$GA4_HOME/bin"
mkdir -p "$GA4_BIN"

cp "$(dirname "$0")/src/ga4_ai/cli.py" "$GA4_HOME/ga4_tool.py"

cat << 'EOF' > "$GA4_BIN/ga4"
#!/usr/bin/env bash
python3 "$HOME/.ga4/ga4_tool.py" "$@"
EOF
chmod +x "$GA4_BIN/ga4"

SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "$GA4_BIN" "$SHELL_RC"; then
        echo "export PATH=\"\$PATH:$GA4_BIN\"" >> "$SHELL_RC"
        echo "[+] Added $GA4_BIN to $SHELL_RC"
    fi
fi

echo ""
echo "[+] Installation complete!"
echo "1. Place credentials as: $GA4_HOME/credentials.json"
echo "2. Run: ga4 auth"
echo "3. Run: ga4 properties"
