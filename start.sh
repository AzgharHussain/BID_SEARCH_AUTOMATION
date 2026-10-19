#!/bin/bash
# ==============================================================================
# GISFY Agentic Procurements Application Launcher
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=========================================================="
echo "🚀 Starting GISFY Agentic Procurements Application..."
echo "=========================================================="

# 0. Ensure environment file exists
if [ ! -f "$BACKEND_DIR/.env" ]; then
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        echo "ℹ️  Creating backend/.env from .env.example..."
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    fi
fi

# Detect Python interpreter
PYTHON_CMD="python3"
if [ -f "$BACKEND_DIR/venv311/bin/python" ]; then
    PYTHON_CMD="$BACKEND_DIR/venv311/bin/python"
elif [ -f "$BACKEND_DIR/venv/bin/python" ]; then
    PYTHON_CMD="$BACKEND_DIR/venv/bin/python"
elif [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$BACKEND_DIR/.venv/bin/python"
fi

# 1. Start FastAPI Backend if not already running on port 8000
if lsof -i :8000 >/dev/null 2>&1; then
    echo "🟢 Backend is already running on http://127.0.0.1:8000"
else
    echo "⏳ Starting FastAPI Backend Server on port 8000 with $PYTHON_CMD..."
    cd "$BACKEND_DIR" || exit 1
    PYTHONUNBUFFERED=1 "$PYTHON_CMD" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info > "$BACKEND_DIR/uvicorn.log" 2>&1 &
    BACKEND_PID=$!
    disown "$BACKEND_PID" 2>/dev/null || true
    
    # Wait up to 15 seconds for backend to be ready
    for i in {1..15}; do
        if curl -s http://127.0.0.1:8000/api/sync/status >/dev/null 2>&1; then
            echo "🟢 Backend started successfully!"
            break
        fi
        sleep 1
    done
fi

# 2. Start Vite Frontend if not already running on port 5173
if lsof -i :5173 >/dev/null 2>&1; then
    echo "🟢 Frontend is already running on http://127.0.0.1:5173"
else
    cd "$FRONTEND_DIR" || exit 1
    # Ensure Node 18/20 is activated via NVM if present
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        . "$NVM_DIR/nvm.sh"
        nvm use 20 >/dev/null 2>&1 || nvm use 18 >/dev/null 2>&1 || true
        NODE_BIN_DIR="$(dirname "$(nvm which current 2>/dev/null || nvm which 20 2>/dev/null)")"
        if [ -d "$NODE_BIN_DIR" ]; then
            export PATH="$NODE_BIN_DIR:$PATH"
        fi
    fi
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo "⏳ Installing frontend dependencies..."
        if command -v yarn >/dev/null 2>&1; then
            yarn install
        else
            npm install
        fi
    fi
    echo "⏳ Starting Vite Frontend Server on port 5173..."
    nohup ./node_modules/.bin/vite --host 0.0.0.0 --port 5173 < /dev/null > "$FRONTEND_DIR/vite.log" 2>&1 &
    FRONTEND_PID=$!
    disown "$FRONTEND_PID" 2>/dev/null || true
    
    # Wait up to 15 seconds for frontend to be ready
    for i in {1..15}; do
        if curl -s http://127.0.0.1:5173 >/dev/null 2>&1; then
            echo "🟢 Frontend started successfully!"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "🌐 Opening Application in your browser..."
if command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:5173"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:5173"
fi

echo "=========================================================="
echo "✅ Application is live at: http://127.0.0.1:5173"
echo "📚 Backend API Docs at:   http://127.0.0.1:8000/docs"
echo "📊 Master Excel Export:   http://127.0.0.1:8000/api/reports/proposals-excel"
echo "=========================================================="
