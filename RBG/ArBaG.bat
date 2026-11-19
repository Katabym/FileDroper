@echo off
cd /d "%~dp0"

REM Активируем виртуальное окружение (если есть)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Виртуальное окружение активировано
)

REM Запускаем скрипт
python main.py

pause