#!/bin/bash

echo "Starting Avenlis React UI Development Server..."
echo ""
echo "Checking if node_modules exists..."

if [ ! -d "node_modules" ]; then
    echo "ERROR: node_modules folder not found!"
    echo "Please copy node_modules from a machine where you ran 'npm install'"
    exit 1
fi

echo "node_modules found, starting development server..."
echo ""
echo "React UI will be available at: http://localhost:3000"
echo "Make sure your Python backend is running on port 8080"
echo ""

# Try different methods to start Vite
if command -v npx &> /dev/null; then
    echo "Using npx to start Vite..."
    npx vite dev --host 0.0.0.0 --port 3000
elif command -v node &> /dev/null; then
    echo "Using node to start Vite directly..."
    if [ -f "node_modules/.bin/vite" ]; then
        node node_modules/.bin/vite dev --host 0.0.0.0 --port 3000
    elif [ -f "node_modules/vite/bin/vite.js" ]; then
        node node_modules/vite/bin/vite.js dev --host 0.0.0.0 --port 3000
    else
        echo "ERROR: Could not find Vite executable"
        exit 1
    fi
else
    echo "ERROR: Node.js not found on this system"
    exit 1
fi



