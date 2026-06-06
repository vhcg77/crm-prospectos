@echo off
REM Runner para Windows sin `just`. Uso: dev.bat [dev|seed|test|build|reset-dev]
REM Construir (build) SIEMPRE desde un venv limpio, NUNCA desde conda/miniforge.

if "%1"=="" goto dev
if "%1"=="dev" goto dev
if "%1"=="seed" goto seed
if "%1"=="test" goto test
if "%1"=="build" goto build
if "%1"=="reset-dev" goto reset
goto end

:dev
set APP_ENV=development
python main.py
goto end

:seed
set APP_ENV=development
python seeds\seed_dev.py
goto end

:test
set APP_ENV=testing
pytest tests\ -v
goto end

:build
pyinstaller crm.spec
goto end

:reset
del /q data\crm_dev.db 2>nul
set APP_ENV=development
python seeds\seed_dev.py
goto end

:end
