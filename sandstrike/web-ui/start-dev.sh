#!/bin/bash
# Start Avenlis development servers

echo "🚀 Starting Avenlis SandStrike Development Environment"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the avenlis/web-ui directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🔧 Starting backend server..."
# Start backend in background
cd ..
python -m avenlis server --host 0.0.0.0 --port 5000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo "⚛️  Starting React development server..."
cd web-ui
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development servers started!"
echo "   React UI: http://localhost:3000"
echo "   Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT

# Wait for user to stop
wait
