@echo off
setlocal enabledelayedexpansion
REM Stage Monitoring Tool — Ontwikkelstartscript
REM Cross-platform: Windows (Command Prompt, PowerShell)
REM Start backend (FastAPI) + frontend (Vite dev server) in één keer
REM
REM Gebruik:
REM   start.bat              Start backend + frontend
REM   start.bat --reset      Reset database + seed
REM   start.bat --backend    Start alleen backend
REM   start.bat --frontend   Start alleen frontend
REM   start.bat --help       Toon help

cd /d "%~dp0"

set "BACKEND_PORT=8001"
set "FRONTEND_PORT=8080"
set "PROJECT_DIR=%CD%"
set "RESET_DB=false"
set "BACKEND_ONLY=false"
set "FRONTEND_ONLY=false"
set "HELP=false"

REM ── Argumenten verwerken ─────────────────────────────────────────────
for %%a in (%*) do (
  if "%%a"=="--reset" set "RESET_DB=true"
  if "%%a"=="--backend" set "BACKEND_ONLY=true"
  if "%%a"=="--frontend" set "FRONTEND_ONLY=true"
  if "%%a"=="--help" set "HELP=true"
  if "%%a"=="-h" set "HELP=true"
)

if "%HELP%"=="true" (
  echo Stage Monitoring Tool — Ontwikkelstartscript
  echo.
  echo Gebruik: start.bat [opties]
  echo.
  echo Opties:
  echo   (geen)       Start backend + frontend
  echo   --reset      Reset database en vul opnieuw met demodata
  echo   --backend    Start alleen backend API server
  echo   --frontend   Start alleen frontend dev server
  echo   --help       Toon deze help
  echo.
  echo Vereisten:
  echo   * Python 3.10+ (met pip of uv)
  echo   * Node.js 18+ (voor Vite dev server)
  echo.
  echo Testaccounts:
  echo   admin@school.be      / demo123
  echo   docent1@school.be    / docent123
  echo   student1@school.be   / student123
  echo.
  pause
  exit /b 0
)

REM ── Python controleren ───────────────────────────────────────────────
where python >nul 2>&1
if !errorlevel! == 0 (
  set "PYTHON_RUNNER=python"
  goto :python_found
)
where py >nul 2>&1
if !errorlevel! == 0 (
  set "PYTHON_RUNNER=py"
  goto :python_found
)
echo.
echo FOUT: Python niet gevonden. Installeer Python via https://python.org
echo.
pause
exit /b 1

:python_found
echo [OK] Python gevonden: !PYTHON_RUNNER!

REM ── Node.js controleren ──────────────────────────────────────────────
if "%BACKEND_ONLY%"=="false" (
  where node >nul 2>&1
  if !errorlevel! neq 0 (
    echo.
    echo FOUT: Node.js niet gevonden. Installeer via https://nodejs.org
    echo        Of voer uit: start.bat --backend  om alleen backend te starten
    echo.
    pause
    exit /b 1
  )
  where npm >nul 2>&1
  if !errorlevel! neq 0 (
    echo.
    echo FOUT: npm niet gevonden. Dit hoort bij Node.js.
    echo.
    pause
    exit /b 1
  )
  echo [OK] Node.js gevonden
)

REM ── .env controleren ─────────────────────────────────────────────────
if not exist "%PROJECT_DIR%\backend\.env" (
  if exist "%PROJECT_DIR%\backend\.env.example" (
    echo [INFO] backend\.env aanmaken uit .env.example...
    for /f "tokens=*" %%l in ('%PYTHON_RUNNER% -c "import secrets; print(secrets.token_hex(32))"') do set "RANDOM_KEY=%%l"
    for /f "tokens=*" %%l in ('%PYTHON_RUNNER% -c "import os; print(os.urandom(32).hex())"') do set "RANDOM_KEY=%%l"
    if "!RANDOM_KEY!"=="" (
      set "RANDOM_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%"
    )
    copy /y "%PROJECT_DIR%\backend\.env.example" "%PROJECT_DIR%\backend\.env" >nul
    powershell -Command "(Get-Content '%PROJECT_DIR%\backend\.env') -replace 'SECRET_KEY=.*', 'SECRET_KEY=!RANDOM_KEY!' | Set-Content '%PROJECT_DIR%\backend\.env'"
    echo [OK] .env aangemaakt met willekeurige SECRET_KEY
  ) else (
    echo [WAARSCHUWING] .env.example niet gevonden. Sommige functies werken mogelijk niet.
  )
)

REM ── uv controleren ───────────────────────────────────────────────────
where uv >nul 2>&1
if !errorlevel! == 0 (
  set "USE_UV=true"
  echo [OK] uv gedetecteerd
) else (
  set "USE_UV=false"
  echo [INFO] uv niet gevonden, gebruik python3
)

REM ── venv controleren ─────────────────────────────────────────────────
if "%USE_UV%"=="true" (
  if not exist "%PROJECT_DIR%\backend\.venv" (
    echo [INFO] Virtuele omgeving aanmaken met uv...
    cd /d "%PROJECT_DIR%\backend"
    uv venv
  )
  set "PYTHON_RUNNER=uv run -- python"
  set "INIT_RUNNER=uv run -- python"
  set "PIP_RUNNER=uv run -- pip"
) else (
  if exist "%PROJECT_DIR%\backend\.venv\Scripts\python.exe" (
    set "PYTHON_RUNNER=%PROJECT_DIR%\backend\.venv\Scripts\python.exe"
    set "INIT_RUNNER=%PROJECT_DIR%\backend\.venv\Scripts\python.exe"
    set "PIP_RUNNER=%PROJECT_DIR%\backend\.venv\Scripts\pip.exe"
  )
)

REM ── Frontend deps installeren ───────────────────────────────────────
if "%BACKEND_ONLY%"=="false" (
  if not exist "%PROJECT_DIR%\frontend\node_modules" (
    echo [INFO] Frontend afhankelijkheden installeren...
    cd /d "%PROJECT_DIR%\frontend"
    call npm install
    if !errorlevel! neq 0 (
      echo [FOUT] npm install mislukt.
      pause
      exit /b 1
    )
    echo [OK] Frontend deps geinstalleerd
  )
)

REM ── Backend deps installeren ──────────────────────────────────────────
echo [INFO] Backend afhankelijkheden controleren...
cd /d "%PROJECT_DIR%\backend"
%PYTHON_RUNNER% -c "import uvicorn, fastapi, sqlalchemy, pydantic, dotenv" >nul 2>&1
if !errorlevel! neq 0 (
  echo [INFO] Backend afhankelijkheden installeren...
  if "%USE_UV%"=="true" (
    uv pip install -r requirements.txt
  ) else (
    %PIP_RUNNER% install -r requirements.txt
  )
  if !errorlevel! neq 0 (
    echo [FOUT] Backend afhankelijkheden installeren mislukt.
    pause
    exit /b 1
  )
  echo [OK] Backend deps geinstalleerd
)

REM ── Database ─────────────────────────────────────────────────────────
set "DB_FILE=%PROJECT_DIR%\backend\stage_monitoring.db"

if "%RESET_DB%"=="true" (
  echo [INFO] Database resetten...
  if exist "%DB_FILE%" (
    del /f "%DB_FILE%"
    echo [OK] Databasebestand verwijderd
  )
)

if not exist "%DB_FILE%" (
  echo [INFO] Database niet gevonden. Tabellen aanmaken...
  %PYTHON_RUNNER% -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('Tabellen aangemaakt.')" >nul 2>&1
  if !errorlevel! neq 0 (
    echo [WAARSCHUWING] Tabellen aanmaken mislukt. Modellen zijn mogelijk nog niet importeerbaar.
  )
  echo [INFO] Database vullen met demodata...
  %INIT_RUNNER% seed_loader.py
  echo [OK] Database gevuld
) else (
  %PYTHON_RUNNER% -c "
import sqlite3, sys
conn = sqlite3.connect('%DB_FILE%')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
conn.close()
if count == 0:
    sys.exit(1)
" >nul 2>&1
  if !errorlevel! neq 0 (
    echo [INFO] Database leeg. Vullen...
    %INIT_RUNNER% seed_loader.py
    echo [OK] Database gevuld
  )
)

REM ── Poort opruimen ────────────────────────────────────────────────────
if "%FRONTEND_ONLY%"=="false" (
  echo [INFO] Poort %BACKEND_PORT% controleren...
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%" ^| findstr "LISTENING"') do (
    echo [INFO] Oude backend PID %%a afsluiten...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 /nobreak >nul
  )
)

if "%BACKEND_ONLY%"=="false" (
  echo [INFO] Poort %FRONTEND_PORT% controleren...
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%" ^| findstr "LISTENING"') do (
    echo [INFO] Oude frontend PID %%a afsluiten...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 /nobreak >nul
  )
)

REM ── Backend starten ──────────────────────────────────────────────────
if "%FRONTEND_ONLY%"=="false" (
  echo [START] Backend starten op http://localhost:%BACKEND_PORT%
  cd /d "%PROJECT_DIR%\backend"
  start "Backend API" cmd /c "%PYTHON_RUNNER% -m uvicorn app.main:app --reload --port %BACKEND_PORT% --host 0.0.0.0"
  timeout /t 2 /nobreak >nul
)

REM ── Frontend starten ─────────────────────────────────────────────────
if "%BACKEND_ONLY%"=="false" (
  echo [START] Frontend starten op http://localhost:%FRONTEND_PORT%
  cd /d "%PROJECT_DIR%\frontend"
  start "Frontend Dev" cmd /c "npm run dev"
  timeout /t 2 /nobreak >nul
)

REM ── Samenvatting ────────────────────────────────────────────────────
echo.
echo ========================================================
echo  Alles draait!
if "%FRONTEND_ONLY%"=="false" (
  echo   Backend:   http://localhost:%BACKEND_PORT%
  echo   API docs:  http://localhost:%BACKEND_PORT%/docs
)
if "%BACKEND_ONLY%"=="false" (
  echo   Frontend:  http://localhost:%FRONTEND_PORT%
)
echo.
echo Testaccounts:
echo   admin@school.be      / demo123
echo   docent1@school.be    / docent123
echo   mentor1@school.be    / mentor123
echo   student1@school.be   / student123
echo   commissie1@school.be / commissie123
echo.
echo Druk op een toets om te stoppen...
echo ========================================================
pause >nul

REM ── Afsluiten ─────────────────────────────────────────────────────────
echo.
echo [INFO] Afsluiten...
if "%FRONTEND_ONLY%"=="false" (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
  )
)
if "%BACKEND_ONLY%"=="false" (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
  )
)
echo [OK] Gestopt.

:done
endlocal
