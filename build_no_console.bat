@echo off
SETLOCAL ENABLEDELAYEDEXECUTION
set APP_NAME=ParserWebNovels
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --clean --noconfirm --onefile --noconsole --name "%APP_NAME%" app.py
echo.
echo [ГОТОВО] dist\%APP_NAME%.exe
pause
