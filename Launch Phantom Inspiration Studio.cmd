@echo off
setlocal
cd /d "%~dp0"

where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama is not installed or is not on PATH.
  echo Install it from https://ollama.com/ then launch this file again.
  pause
  exit /b 1
)

curl --silent --max-time 2 http://127.0.0.1:11434/api/tags >nul 2>nul
if errorlevel 1 (
  start "Phantom - Ollama" /min ollama serve
  timeout /t 2 /nobreak >nul
)

if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing: .venv\Scripts\python.exe
  pause
  exit /b 1
)

start "Phantom Inspiration Studio" /d "%CD%" ".venv\Scripts\python.exe" "main.py"
endlocal
