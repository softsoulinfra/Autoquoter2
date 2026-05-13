#!/bin/bash
echo "Starting SoftSoul Infra E-Quoter..."
DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any existing instances
kill $(lsof -t -i:8080) 2>/dev/null
kill $(lsof -t -i:8000) 2>/dev/null
sleep 1

# Start backend
cd "$DIR/server"
python3 main.py &
BACKEND_PID=$!
echo "Backend starting on http://localhost:8000 (PID: $BACKEND_PID)"

# Start frontend
cd "$DIR"
python3 -m http.server 8080 &
FRONTEND_PID=$!
echo "Frontend starting on http://localhost:8080 (PID: $FRONTEND_PID)"

sleep 3

# Verify
echo ""
curl -s http://localhost:8000/api/health > /dev/null && echo "✓ Backend is running" || echo "✗ Backend failed"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 > /dev/null && echo "✓ Frontend is running" || echo "✗ Frontend failed"

echo ""
echo "─" Open http://localhost:8080 in your browser
echo ""
wait
