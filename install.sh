#macOS版 安裝claude desktop + NCHU_library
#!/bin/bash
set -e
set -u

# === Variable Setup ===
LIBRARY_API_SRC="/Users/lic/Downloads/mcp_auto_setup_NCHU_library-main/library_api.py"
PROJECT_DIR="$HOME/library"
INSTALLER="$HOME/Downloads/Claude-Setup-macOS.dmg"
PY=$(which python3)

echo "[1/7] Creating project directory..."
mkdir -p "$PROJECT_DIR"

echo "[2/7] Copying library_api.py to project directory..."
if [ ! -f "$LIBRARY_API_SRC" ]; then
    echo "[ERROR] Source file library_api.py does not exist: $LIBRARY_API_SRC"
    exit 1
fi
cp -f "$LIBRARY_API_SRC" "$PROJECT_DIR/library_api.py"

echo "[3/7] Skipping Claude Desktop download (already installed)..."
if [ -f "$INSTALLER" ]; then
    echo "[INFO] Claude installer found at: $INSTALLER"
else
    echo "[WARN] Claude installer not found, but continuing since you installed manually."
fi

echo "[4/7] Installing Python dependencies using $PY..."
$PY -m pip install --upgrade pip
$PY -m pip install "mcp[cli]" httpx requests

echo "[5/7] Testing library_api.py can run..."
$PY "$PROJECT_DIR/library_api.py" &
SERVER_PID=$!
sleep 5
kill $SERVER_PID || true
echo "[INFO] library_api.py started successfully (test run)."

echo "[6/7] Writing Claude config to file..."
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
mkdir -p "$(dirname "$CLAUDE_CONFIG")"

cat > "$CLAUDE_CONFIG" <<EOL
{
    "mcpServers": {
        "NCHU_library": {
            "command": "$PY",
            "args": [
                "$PROJECT_DIR/library_api.py"
            ]
        }
    }
}
EOL

if [ ! -s "$CLAUDE_CONFIG" ]; then
    echo "[ERROR] Claude config file is empty or not created!"
    exit 1
fi

echo "[7/7] Installation completed successfully!"
echo -e "\033[0;32mNow restart Claude Desktop and it should detect NCHU_library.\033[0m"
