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

where python >nul 2>&1 || (
  echo Python не найден в PATH.
  exit /b 1
)
python -m pip install --upgrade pip || exit /b 1
if exist requirements.txt (
  pip install -r requirements.txt || exit /b 1
) else (
  echo requirements.txt не найден.
)

REM Если есть spec, удалим перед чистой сборкой
if exist DeepParser.spec del /f /q DeepParser.spec

pyinstaller --clean --noconfirm --name DeepParser --onefile --windowed app.py || exit /b 1

exit /b %ERRORLEVEL%
