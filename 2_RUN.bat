@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "APP_PATH=%~dp0"
echo Using directory: %APP_PATH%

set "VENV_PATH=%APP_PATH%.venv"
set "VENV_PYTHON=%VENV_PATH%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Virtual environment not found. Please run setup.bat first.
    goto error
)

if "%VIRTUAL_ENV%"=="" (
    call "%VENV_PATH%\Scripts\activate.bat"
)

cls

set "APPLICATION_FILE=%APP_PATH%main.py"
echo ========================================
echo #                                      #
echo #      Starting Python application     #
echo #                                      #
echo ========================================

if exist "%APPLICATION_FILE%" (
    "%VENV_PYTHON%" "%APPLICATION_FILE%"
) else (
    echo ERROR: Application file not found at:
    echo %APPLICATION_FILE%
    goto error
)

echo ========================================
echo #                                      #
echo #        Application closed            #
echo #                                      #
echo ========================================
pause
goto eof

:error
echo ========================================
echo #                                      #
echo #          Error occurred              #
echo #                                      #
echo ========================================
pause
:eof
endlocal
