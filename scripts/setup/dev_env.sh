#!/bin/bash
# Development environment bootstrap (Mac/Linux)
# Usage: ./scripts/setup/dev_env.sh

set -e

cd "$(dirname "$0")/../.."

echo "═══════════════════════════════════════════════════════════"
echo "Development Environment Setup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check Python
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✓ Python: $PYTHON_VERSION"
else
    echo "✗ Python 3 not found. Install from https://www.python.org/"
    exit 1
fi

# Check Node.js
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js: $NODE_VERSION"
else
    echo "✗ Node.js not found. Install from https://nodejs.org/"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ npm: $NPM_VERSION"
else
    echo "✗ npm not found"
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
if [ -f "backend/requirements.txt" ]; then
    python3 -m pip install --user -r backend/requirements.txt
    echo "✓ Python dependencies installed"
else
    echo "⚠ backend/requirements.txt not found"
fi

echo ""
echo "Installing Node.js dependencies..."
if [ -f "frontend/package.json" ]; then
    cd frontend
    npm install
    cd ..
    echo "✓ Node.js dependencies installed"
else
    echo "⚠ frontend/package.json not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Recommended VS Code / Cursor Extensions"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Install these extensions for best experience:"
echo "  - dbaeumer.vscode-eslint (ESLint)"
echo "  - esbenp.prettier-vscode (Prettier)"
echo "  - ms-python.python (Python)"
echo "  - yzhang.markdown-all-in-one (Markdown)"
echo ""
echo "Extensions are recommended in .vscode/extensions.json"
echo "VS Code/Cursor should prompt you to install them."
echo ""
echo "⚠ Note: App-level Cursor settings (keybindings, themes, etc.)"
echo "  cannot be synced across different Cursor accounts via git."
echo "  Use repo-level configs (.vscode/settings.json) as source of truth."
echo ""
echo "✓ Setup complete!"

