@echo off
REM Start Avenlis development servers - Windows version

echo 🚀 Starting Avenlis SandStrike Development Environment
echo.

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Please run this script from the sandstrike/web-ui directory
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

echo 🔧 Starting backend server...
REM Start backend in new window
cd ..
start "Avenlis Backend" cmd /k "python -m sandstrike.server --host 0.0.0.0 --port 8080"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo ⚛️  Starting React development server...
cd web-ui
start "Avenlis Frontend" cmd /k "npm run dev"

echo.
echo ✅ Development servers started!
echo    React UI: http://localhost:3000
echo    Backend:  http://localhost:8080
echo.
echo Two command windows have opened. Close them to stop the servers.
pause
