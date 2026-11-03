@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
  echo Falta Node.js 22 o posterior. Instalalo desde https://nodejs.org/
  pause
  exit /b 1
)
node scripts\launch.cjs
if errorlevel 1 (
  pause
  exit /b 1
)
endlocal
