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
@echo off
setlocal ENABLEDELAYEDEXPANSION
title Установка M3.1 (патч поверх вашей папки)

echo [1/6] Проверяю наличие base64: PATCH_M3_1.b64.txt
if not exist "PATCH_M3_1.b64.txt" (
  echo [ОШИБКА] Нет файла PATCH_M3_1.b64.txt рядом с этим батником.
  echo Скачай также PATCH_M3_1.b64.txt и положи рядом.
  pause
  exit /b 1
)

echo [2/6] Декодирую архив патча...
set PATCH_ZIP=PATCH_M3_1.zip
powershell -NoProfile -Command "$b=[IO.File]::ReadAllText('PATCH_M3_1.b64.txt');$d=[Convert]::FromBase64String($b);[IO.File]::WriteAllBytes('%PATCH_ZIP%',$d)"
if not exist "%PATCH_ZIP%" (
  echo [ОШИБКА] Не удалось создать %PATCH_ZIP%
  pause
  exit /b 1
)

echo [3/6] Создаю резервную копию текущей папки (backup_M3_1)
set BK=backup_M3_1
if not exist "%BK%" mkdir "%BK%"
for %%F in (app.py site_profiles.py utils_docx.py ParserWebNovels.spec requirements.txt) do (
  if exist "%%F" copy /y "%%F" "%BK%\%%F" >nul
)

echo [4/6] Распаковываю патч в текущую папку...
powershell -NoProfile -Command "Expand-Archive -Path '%PATCH_ZIP%' -DestinationPath '.' -Force"

echo [5/6] Устанавливаю зависимости...
if not exist ".venv" (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
if exist requirements.txt (
  pip install -r requirements.txt
) else (
  pip install PySide6 requests beautifulsoup4 lxml python-docx google-genai langdetect
)

echo [6/6] Запускаю приложение в dev-режиме...
if exist 02_run_dev.bat (
  call 02_run_dev.bat
) else (
  python app.py
)

echo [ГОТОВО] Если всё ок, собери .exe через 03_build_no_console.bat
pause

exit /b %ERRORLEVEL%
