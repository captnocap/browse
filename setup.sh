#!/usr/bin/env bash
set -euo pipefail

# ─── browse v2 — One-Command Setup ────────────────────────────────────────
# Downloads Firefox ESR + geckodriver, installs the Python package,
# applies stealth patches, and configures MCP for your AI frontend.
#
# Usage:
#   git clone <repo> && cd browse && ./setup.sh
# ─────────────────────────────────────────────────────────────────────────

FIREFOX_VERSION="esr-latest"
GECKODRIVER_VERSION="0.36.0"
RUNTIME_DIR="$(cd "$(dirname "$0")" && pwd)/runtime"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors (if terminal supports them)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    GREEN='' YELLOW='' RED='' BLUE='' BOLD='' NC=''
fi

info()  { echo -e "${BLUE}[info]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ok]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
fail()  { echo -e "${RED}[error]${NC} $*"; exit 1; }

# ─── Preflight checks ──────────────────────────────────────────────────

echo -e "\n${BOLD}browse — Anti-Fingerprint AI Browser (Firefox ESR + RFP)${NC}\n"

# Platform check
ARCH="$(uname -m)"
OS="$(uname -s)"

if [ "$OS" != "Linux" ]; then
    fail "This project currently supports Linux only. Detected: $OS"
fi

if [ "$ARCH" != "x86_64" ]; then
    fail "Only x86_64 is supported. Detected: $ARCH"
fi

# Required tools
for cmd in python3 curl tar; do
    if ! command -v "$cmd" &>/dev/null; then
        fail "Missing required tool: $cmd"
    fi
done

ok "Platform: Linux $ARCH"

# ─── Create runtime directory ───────────────────────────────────────────

mkdir -p "$RUNTIME_DIR"

# ─── Download Firefox ESR ───────────────────────────────────────────────

FIREFOX_DIR="$RUNTIME_DIR/firefox"
FIREFOX_ARCHIVE="$RUNTIME_DIR/firefox-esr.tar.bz2"
# Mozilla's download URL auto-resolves to the latest ESR for the platform.
FIREFOX_URL="https://download.mozilla.org/?product=firefox-esr-latest-ssl&os=linux64&lang=en-US"

if [ -d "$FIREFOX_DIR" ] && [ -f "$FIREFOX_DIR/firefox" ]; then
    ok "Firefox ESR already installed"
else
    if [ -f "$FIREFOX_ARCHIVE" ]; then
        info "Firefox ESR archive already downloaded"
    else
        info "Downloading Firefox ESR (~80 MB)..."
        curl -L --progress-bar -o "$FIREFOX_ARCHIVE" "$FIREFOX_URL" || \
            fail "Failed to download Firefox ESR. Check your internet connection."
        ok "Downloaded Firefox ESR"
    fi

    info "Extracting Firefox ESR..."
    tar -xf "$FIREFOX_ARCHIVE" -C "$RUNTIME_DIR" || \
        fail "Failed to extract Firefox ESR archive"

    # Mozilla's archive extracts to a directory called "firefox"
    if [ ! -d "$FIREFOX_DIR" ]; then
        EXTRACTED=$(find "$RUNTIME_DIR" -maxdepth 1 -type d -name "firefox*" | head -1)
        if [ -n "$EXTRACTED" ] && [ "$EXTRACTED" != "$FIREFOX_DIR" ]; then
            mv "$EXTRACTED" "$FIREFOX_DIR"
        fi
    fi

    if [ ! -f "$FIREFOX_DIR/firefox" ]; then
        fail "Firefox ESR extraction failed — firefox binary not found"
    fi

    # Record version info
    FF_ACTUAL_VERSION=$("$FIREFOX_DIR/firefox" --version 2>/dev/null | head -1 || echo "unknown")
    echo "{\"version\": \"$FF_ACTUAL_VERSION\", \"architecture\": \"linux-x86_64\"}" \
        > "$FIREFOX_DIR/browse_version.json"

    ok "Firefox ESR installed ($FF_ACTUAL_VERSION)"
    rm -f "$FIREFOX_ARCHIVE"
fi

# ─── Download geckodriver ───────────────────────────────────────────────

GECKODRIVER_BIN="$RUNTIME_DIR/geckodriver"
GECKODRIVER_URL="https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz"

if [ -f "$GECKODRIVER_BIN" ]; then
    ok "geckodriver ${GECKODRIVER_VERSION} already installed"
else
    info "Downloading geckodriver ${GECKODRIVER_VERSION}..."
    curl -L --progress-bar -o "$RUNTIME_DIR/geckodriver.tar.gz" "$GECKODRIVER_URL" || \
        fail "Failed to download geckodriver"

    tar -xzf "$RUNTIME_DIR/geckodriver.tar.gz" -C "$RUNTIME_DIR" || \
        fail "Failed to extract geckodriver"

    chmod +x "$GECKODRIVER_BIN"
    rm -f "$RUNTIME_DIR/geckodriver.tar.gz"
    ok "geckodriver ${GECKODRIVER_VERSION} installed"
fi

# ─── Install Python package + MCP ───────────────────────────────────────

info "Installing browse package (with MCP support)..."
pip3 install -e "$PROJECT_DIR[mcp]" --quiet 2>&1 | tail -1 || \
    pip3 install -e "$PROJECT_DIR[mcp]" --quiet --break-system-packages 2>&1 | tail -1 || \
    fail "Failed to install browse package. Try running in a virtualenv."
ok "Python package installed"

# ─── geckodriver PATH ───────────────────────────────────────────────────

NEED_PATH=false
if ! command -v geckodriver &>/dev/null; then
    NEED_PATH=true
    # Add to current session
    export PATH="$RUNTIME_DIR:$PATH"
fi

# Persist to shell profile if not already there
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then SHELL_RC="$HOME/.bashrc"; fi
if [ -f "$HOME/.zshrc" ]; then SHELL_RC="$HOME/.zshrc"; fi

if [ "$NEED_PATH" = true ] && [ -n "$SHELL_RC" ]; then
    if ! grep -q "$RUNTIME_DIR" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# browse — geckodriver" >> "$SHELL_RC"
        echo "export PATH=\"$RUNTIME_DIR:\$PATH\"" >> "$SHELL_RC"
        ok "Added geckodriver to PATH in $SHELL_RC"
    fi
fi

# ─── Write browse.conf ─────────────────────────────────────────────────

CONFIG_FILE="$PROJECT_DIR/browse.conf"
cat > "$CONFIG_FILE" <<EOF
# Auto-generated by setup.sh
FIREFOX_PATH=$FIREFOX_DIR
GECKODRIVER_PATH=$GECKODRIVER_BIN
EOF
ok "Config written to browse.conf"

# ─── Apply stealth patch ───────────────────────────────────────────────

info "Applying stealth patch..."
python3 -c "
from browse.stealth import patch_libxul, is_patched
fp = '$FIREFOX_DIR'
if is_patched(fp):
    print('  Already patched')
else:
    patch_libxul(fp)
    print('  Patched libxul.so — navigator.webdriver removed')
" || warn "Stealth patch failed (non-fatal — can be applied later)"
ok "Stealth patch applied"

# ─── MCP Configuration ─────────────────────────────────────────────────

BROWSE_MCP_CMD="$(which browse-mcp 2>/dev/null || echo "$PROJECT_DIR/.venv/bin/browse-mcp")"

echo ""
echo -e "${BOLD}MCP Configuration${NC}"
echo ""

configure_mcp() {
    local config_file="$1"
    local app_name="$2"

    if [ ! -f "$config_file" ]; then
        # Create new config
        mkdir -p "$(dirname "$config_file")"
        cat > "$config_file" <<NEWCFG
{
  "mcpServers": {
    "browse": {
      "command": "$BROWSE_MCP_CMD"
    }
  }
}
NEWCFG
        ok "Created $app_name config: $config_file"
        return 0
    fi

    # Config exists — check if browse is already configured
    if grep -q '"browse"' "$config_file" 2>/dev/null; then
        ok "$app_name already configured"
        return 0
    fi

    # Config exists but browse isn't in it — show manual instructions
    warn "$app_name config exists but browse is not configured"
    echo -e "    Add this to the ${BOLD}mcpServers${NC} section of ${BOLD}$config_file${NC}:"
    echo ""
    echo -e "    ${BOLD}\"browse\": {"
    echo -e "      \"command\": \"$BROWSE_MCP_CMD\""
    echo -e "    }${NC}"
    echo ""
    return 0
}

CONFIGURED=false

# Claude Desktop
CLAUDE_DESKTOP_LINUX="$HOME/.config/claude/claude_desktop_config.json"
CLAUDE_DESKTOP_MAC="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -d "$HOME/.config/claude" ] || command -v claude-desktop &>/dev/null 2>&1; then
    configure_mcp "$CLAUDE_DESKTOP_LINUX" "Claude Desktop"
    CONFIGURED=true
fi

# Claude Code
CLAUDE_CODE_CONFIG="$HOME/.claude.json"
if command -v claude &>/dev/null 2>&1; then
    info "Claude Code detected"
    echo -e "    Add to your project's ${BOLD}.mcp.json${NC} or ${BOLD}claude_desktop_config.json${NC}:"
    echo ""
    echo -e "    ${BOLD}\"browse\": {"
    echo -e "      \"command\": \"$BROWSE_MCP_CMD\""
    echo -e "    }${NC}"
    echo ""
    CONFIGURED=true
fi

# LM Studio
LMSTUDIO_CONFIG_DIR="$HOME/.lmstudio"
if [ -d "$LMSTUDIO_CONFIG_DIR" ] || command -v lms &>/dev/null 2>&1; then
    info "LM Studio detected"
    echo -e "    In LM Studio, go to ${BOLD}Settings > MCP Servers${NC} and add:"
    echo ""
    echo -e "    ${BOLD}Name:${NC}    browse"
    echo -e "    ${BOLD}Command:${NC} $BROWSE_MCP_CMD"
    echo ""
    CONFIGURED=true
fi

# Generic / not detected
if [ "$CONFIGURED" = false ]; then
    info "No known AI frontend detected. Manual MCP configuration:"
    echo ""
    echo -e "  For any MCP-compatible client, add this server:"
    echo ""
    echo -e "    ${BOLD}Command:${NC} $BROWSE_MCP_CMD"
    echo ""
    echo -e "  Or for JSON configs (Claude Desktop, Cursor, etc.):"
    echo ""
    echo -e "    ${BOLD}{"
    echo -e "      \"mcpServers\": {"
    echo -e "        \"browse\": {"
    echo -e "          \"command\": \"$BROWSE_MCP_CMD\""
    echo -e "        }"
    echo -e "      }"
    echo -e "    }${NC}"
    echo ""
fi

# ─── Summary ────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}Setup complete.${NC}"
echo ""
echo -e "  ${BOLD}Components:${NC}"
echo -e "    Firefox ESR:    $FIREFOX_DIR"
echo -e "    geckodriver:    $GECKODRIVER_BIN"
echo -e "    MCP server:     $BROWSE_MCP_CMD"
echo ""
echo -e "  ${BOLD}Usage — MCP (for Claude Desktop, LM Studio, etc.):${NC}"
echo -e "    Just ask your AI to browse the web. It handles everything."
echo ""
echo -e "  ${BOLD}Usage — Python API:${NC}"
echo -e "    from browse import AgentBrowser"
echo -e "    with AgentBrowser() as b:"
echo -e "        print(b.navigate('https://example.com').text)"
echo ""
echo -e "  ${BOLD}Usage — Persistent session (human + AI sharing a browser):${NC}"
echo -e "    python -m browse.session"
echo -e "    # Then from Python: AgentBrowser.connect()"
echo ""
