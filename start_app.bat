@echo off
echo Starting Teaching Assistant...

:: Start Backend in a new window
echo Starting Backend Server...
start "Teaching Assistant Backend" cmd /k "uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

:: Start Frontend in a new window
echo Starting Frontend Server...
cd frontend
start "Teaching Assistant Frontend" cmd /k "npm run dev"

echo System Online! 
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000
