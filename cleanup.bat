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

for /d /r %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del /f /q *.spec
if exist logs rd /s /q logs
if exist .pytest_cache rd /s /q .pytest_cache
echo Очистка завершена.

exit /b %ERRORLEVEL%
