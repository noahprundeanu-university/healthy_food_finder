#!/bin/bash

# Script to fix a broken virtual environment (no sudo required)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "🔧 Fixing virtual environment (no sudo required)..."

if [ -d "$VENV_DIR" ]; then
    echo "Removing existing venv..."
    rm -rf "$VENV_DIR"
fi

echo "Creating new virtual environment..."
python3 -m venv "$VENV_DIR" --without-pip 2>/dev/null || python3 -m venv "$VENV_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment."
    exit 1
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Ensure pip is installed (no sudo required)
if [ ! -f "$VENV_PIP" ]; then
    echo "Installing pip in virtual environment..."
    "$VENV_PYTHON" -m ensurepip --upgrade --default-pip 2>/dev/null || {
        echo "ensurepip failed, downloading get-pip.py..."
        curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        if [ $? -eq 0 ]; then
            "$VENV_PYTHON" /tmp/get-pip.py
        else
            echo "❌ Failed to download get-pip.py"
            exit 1
        fi
    }
fi

# Check if pip is available
if [ ! -f "$VENV_PIP" ] && [ -f "$VENV_DIR/bin/pip3" ]; then
    VENV_PIP="$VENV_DIR/bin/pip3"
fi

# Upgrade pip
echo "Upgrading pip..."
"$VENV_PIP" install --upgrade pip --quiet 2>/dev/null || "$VENV_PIP" install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
"$VENV_PIP" install -r "$PROJECT_DIR/requirements.txt"

if [ $? -eq 0 ]; then
    echo "✅ Virtual environment fixed and dependencies installed!"
else
    echo "❌ Failed to install dependencies."
    exit 1
fi
