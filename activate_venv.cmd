@echo off

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
    exit /b
)

if exist backend\venv\Scripts\activate.bat (
    call backend\venv\Scripts\activate.bat
    echo Virtual environment activated.
    exit /b
)

echo ❌ No venv found. Create one with: python -m venv venv
