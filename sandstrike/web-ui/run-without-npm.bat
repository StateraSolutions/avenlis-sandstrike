@echo off
echo Starting Avenlis React UI Development Server...
echo.
echo Checking if node_modules exists...

if not exist "node_modules" (
    echo ERROR: node_modules folder not found!
    echo Please copy node_modules from a machine where you ran "npm install"
    pause
    exit /b 1
)

echo node_modules found, starting development server...
echo.
echo React UI will be available at: http://localhost:3000
echo Make sure your Python backend is running on port 8080
echo.

REM Try different methods to start Vite
npx vite dev --host 0.0.0.0 --port 3000 2>nul || (
    echo npx not available, trying direct node execution...
    node node_modules\.bin\vite dev --host 0.0.0.0 --port 3000 2>nul || (
        echo Trying alternative node execution...
        node node_modules\vite\bin\vite.js dev --host 0.0.0.0 --port 3000 2>nul || (
            echo ERROR: Could not start Vite development server
            echo Please ensure Node.js is available on this system
            pause
            exit /b 1
        )
    )
)

pause



