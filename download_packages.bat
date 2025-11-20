@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ========================================
echo #                                      #
echo #   Download Packages for Offline     #
echo #        Installation                  #
echo #                                      #
echo ========================================
echo.

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
rem Force use of ANSYS 25.1 (DISABLED - for future use)
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
) else (
    echo Found ANSYS EM v!MAX_VERSION! at: "!ANSYS_ROOT_RECENT!"
)

echo "!ANSYS_ROOT_RECENT!" | findstr /i "Program Files" >nul
if errorlevel 1 (
    echo ANSYS root path is not in Program Files. Aborting.
    goto error
)

set "PYTHON_EXE=!ANSYS_ROOT_RECENT!\commonfiles\CPython\3_10\winx64\Release\python\python.exe"

if not exist "!PYTHON_EXE!" (
    echo Python not found at expected location:
    echo "!PYTHON_EXE!"
    goto error
)

echo Using Python: "!PYTHON_EXE!"

set "PACKAGES_DIR=%APP_PATH%packages"
set "REQUIREMENTS_FILE=%APP_PATH%requirements.txt"

if not exist "%REQUIREMENTS_FILE%" (
    echo requirements.txt not found.
    goto error
)

if not exist "%PACKAGES_DIR%" (
    echo Creating packages directory...
    mkdir "%PACKAGES_DIR%"
)

echo.
echo ========================================
echo Downloading packages to: "%PACKAGES_DIR%"
echo ========================================
echo.

"!PYTHON_EXE!" -m pip download -r "%REQUIREMENTS_FILE%" -d "%PACKAGES_DIR%" || goto error

echo.
echo ========================================
echo #                                      #
echo #   Download completed successfully    #
echo #                                      #
echo ========================================
echo.
echo All packages have been downloaded to the packages folder.
echo You can now distribute this folder with the application.
echo.
pause
goto eof

:error
echo ========================================
echo #                                      #
echo #        Download failed               #
echo #                                      #
echo ========================================
pause
:eof
endlocal
