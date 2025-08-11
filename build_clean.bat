@echo off
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul
echo [OK] Очистка завершена.
pause
