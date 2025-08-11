@echo off
setlocal enabledelayedexpansion
title DeepParser Utility
call :main
set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE% NEQ 0 (
  echo [ERROR] Завершено с ошибкой. Код: %EXITCODE%
) else (
  echo [OK] Готово без ошибок.
)
echo.
echo Нажмите любую клавишу, чтобы закрыть окно...
pause > nul
exit /b %EXITCODE%

:main

if not exist .venv (
  python -m venv .venv || exit /b 1
)
call .venv\Scripts\activate || exit /b 1
if exist requirements.txt (
  pip install -r requirements.txt || exit /b 1
)
python app.py

exit /b %ERRORLEVEL%
