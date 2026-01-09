@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "APP_PATH=%~dp0"
echo Using directory: %APP_PATH%

set "MAX_VERSION=0"
set "FOUND_ANSYS=0"

for /f "tokens=1,2* delims==" %%a in ('set') do (
    set "KEY=%%a"
    if "!KEY:~0,12!"=="ANSYSEM_ROOT" (
        set "VERSION_STR=!KEY:~12!"
        if !VERSION_STR! GTR !MAX_VERSION! (
            set "MAX_VERSION=!VERSION_STR!"
            set "ANSYS_ROOT_RECENT=%%b"
            set "FOUND_ANSYS=1"
        )
    )
)

rem ========================================
rem Force use of ANSYS 25.1 (DISABLED)
rem ========================================
rem set "FORCED_VERSION=251"
rem if defined ANSYSEM_ROOT%FORCED_VERSION% (
rem     set "ANSYS_ROOT_RECENT=!ANSYSEM_ROOT%FORCED_VERSION%!"
rem     set "MAX_VERSION=%FORCED_VERSION%"
rem     set "FOUND_ANSYS=1"
rem     echo Forcing ANSYS EM v25.1 at "!ANSYS_ROOT_RECENT!"
rem ) else (
rem     echo ANSYSEM_ROOT251 not found in environment variables.
rem     goto error
rem )
rem ========================================

if !FOUND_ANSYS! EQU 0 (
    echo No ANSYS EM installation found in environment variables.
    goto error
)

echo Found ANSYS EM v!MAX_VERSION! at: "!ANSYS_ROOT_RECENT!"

set "PYTHON_EXE=!ANSYS_ROOT_RECENT!\commonfiles\CPython\3_10\winx64\Release\python\python.exe"

if not exist "!PYTHON_EXE!" (
    echo Python not found at expected location:
    echo "!PYTHON_EXE!"
    goto error
)

echo Using Python: "!PYTHON_EXE!"

set "VENV_PATH=%APP_PATH%.venv"
set "VENV_PYTHON=%VENV_PATH%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Creating virtual environment...
    "!PYTHON_EXE!" -m venv "%VENV_PATH%" || goto error
    echo Virtual environment created.
)

if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    call "%VENV_PATH%\Scripts\activate.bat" || goto error
)

if "%VIRTUAL_ENV%"=="" (
    echo Failed to activate virtual environment.
    goto error
)

echo.
echo Python version:
python --version || goto error
echo Pip version:
pip --version || goto error

set "REQUIREMENTS_FILE=%APP_PATH%requirements.txt"
set "PACKAGES_DIR=%APP_PATH%packages"

if not exist "%REQUIREMENTS_FILE%" (
    echo requirements.txt not found.
    goto error
)

if exist "%PACKAGES_DIR%" (
    echo.
    echo ========================================
    echo   Offline installation mode detected
    echo ========================================
    echo Installing packages from: "%PACKAGES_DIR%"
    echo.
    pip --require-virtualenv install --no-index --find-links "%PACKAGES_DIR%" -r "%REQUIREMENTS_FILE%" || goto error
    echo.
    echo Offline installation completed.
    echo You can now delete the packages folder as it is no longer needed.
) else (
    echo.
    echo ========================================
    echo   Online installation mode
    echo ========================================
    echo Installing packages from internet...
    echo.
    pip --require-virtualenv --no-cache-dir install -r "%REQUIREMENTS_FILE%" || goto error
    echo.
    echo Online installation completed.
)

echo.
echo ========================================
echo #                                      #
echo #   Setup completed successfully       #
echo #                                      #
echo ========================================
echo.
echo You can now run the application using run.bat
echo.
pause
goto eof

:error
echo.
echo ========================================
echo #                                      #
echo #          Setup failed                #
echo #                                      #
echo ========================================
echo.
pause

:eof
endlocal