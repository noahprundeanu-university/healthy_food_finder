#!/bin/bash

# Start script for Healthy Food Finder
# This script starts both the backend and frontend servers

echo "🥗 Starting Healthy Food Finder..."

# Check if venv module is available
if ! python3 -c "import venv" 2>/dev/null; then
    echo "⚠️  Warning: venv module not available."
    echo "   Trying to proceed anyway..."
    echo ""
fi

# Get absolute path to project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
USE_PYTHON_PIP=false

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" --without-pip 2>/dev/null || python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment."
        echo "   Python venv module may not be available."
        exit 1
    fi
fi

# Verify venv was created correctly
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment Python not found at $VENV_PYTHON"
    echo "   Removing broken venv and recreating..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ] || [ ! -f "$VENV_PYTHON" ]; then
        echo "❌ Failed to create working virtual environment."
        exit 1
    fi
fi

# Ensure pip is installed in venv (works without sudo)
if [ ! -f "$VENV_PIP" ]; then
    echo "Installing pip in virtual environment (no sudo required)..."
    "$VENV_PYTHON" -m ensurepip --upgrade --default-pip 2>/dev/null || {
        echo "ensurepip failed, trying alternative method..."
        # Download get-pip.py if ensurepip doesn't work
        if [ ! -f "/tmp/get-pip.py" ]; then
            echo "Downloading get-pip.py..."
            curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py || {
                echo "❌ Failed to download get-pip.py"
                echo "   Please check your internet connection"
                exit 1
            }
        fi
        "$VENV_PYTHON" /tmp/get-pip.py --user 2>/dev/null || "$VENV_PYTHON" /tmp/get-pip.py
    }
    
    # Check if pip is now available
    if [ ! -f "$VENV_PIP" ]; then
        # Try to find pip in common locations
        if [ -f "$VENV_DIR/bin/pip3" ]; then
            VENV_PIP="$VENV_DIR/bin/pip3"
        elif "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
            # Use python -m pip instead
            VENV_PIP="python -m pip"
            USE_PYTHON_PIP=true
        else
            echo "❌ Failed to install pip in virtual environment."
            echo "   pip is required but couldn't be installed automatically."
            exit 1
        fi
    fi
fi

# Function to install with pip (handles both direct pip and python -m pip)
install_with_pip() {
    if [ "$USE_PYTHON_PIP" = "true" ]; then
        "$VENV_PYTHON" -m pip "$@"
    else
        "$VENV_PIP" "$@"
    fi
}

# Upgrade pip to latest version
echo "Upgrading pip..."
install_with_pip install --upgrade pip --quiet 2>/dev/null || install_with_pip install --upgrade pip

# Install Python dependencies if needed
if [ ! -f "$VENV_DIR/.deps_installed" ]; then
    echo "Installing Python dependencies..."
    install_with_pip install -r "$PROJECT_DIR/requirements.txt"
    if [ $? -eq 0 ]; then
        touch "$VENV_DIR/.deps_installed"
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies."
        exit 1
    fi
else
    # Verify Flask is installed (in case .deps_installed exists but deps aren't actually there)
    if ! "$VENV_PYTHON" -c "import flask" 2>/dev/null; then
        echo "Dependencies appear missing, reinstalling..."
        rm -f "$VENV_DIR/.deps_installed"
        install_with_pip install -r "$PROJECT_DIR/requirements.txt"
        if [ $? -eq 0 ]; then
            touch "$VENV_DIR/.deps_installed"
            echo "✅ Dependencies installed successfully"
        else
            echo "❌ Failed to install dependencies."
            exit 1
        fi
    fi
fi

# Check if node_modules exists
if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo "Installing Node dependencies..."
    cd "$PROJECT_DIR/frontend"
    npm install
    cd "$PROJECT_DIR"
fi

# Start backend in background
echo "Starting backend server on http://localhost:5000..."
cd "$PROJECT_DIR/backend"
"$VENV_PYTHON" app.py &
BACKEND_PID=$!
cd "$PROJECT_DIR"

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "Starting frontend server on http://localhost:3000..."
cd "$PROJECT_DIR/frontend"
npm start &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

echo ""
echo "✅ Servers started!"
echo "   Backend:  http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
