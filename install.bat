@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   Juanita CLI — Instalacion
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python no encontrado.
    echo   Descargalo desde: https://python.org/downloads/
    echo   Marca "Add Python to PATH" al instalarlo.
    pause
    exit /b 1
)

:: Verificar pip
where pip >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip no encontrado.
    echo   Ejecuta: python -m ensurepip --upgrade
    pause
    exit /b 1
)

echo [*] Python detectado correctamente.
echo.

:: Obtener directorio de instalacion
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%CD%\"

:: Instalar dependencias
echo [*] Instalando dependencias...
pip install -q -r "%SCRIPT_DIR%requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.
echo.

:: Crear directorio en AppData
set "APP_DIR=%LOCALAPPDATA%\juanita-cli"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

:: Copiar script
copy /Y "%SCRIPT_DIR%juanita.py" "%APP_DIR%\juanita.py" >nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] No se pudo copiar juanita.py.
    pause
    exit /b 1
)

:: Crear batch wrapper para el PATH del usuario
set "BIN_DIR=%USERPROFILE%\.juanita-bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

>"%BIN_DIR%\juanita.cmd" (
    echo @echo off
    echo python "%APP_DIR%\juanita.py" %%*
)

:: Agregar al PATH de usuario si no esta
echo %PATH% | findstr /C:"%BIN_DIR%" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Agregando %BIN_DIR% al PATH de usuario...
    setx PATH "%BIN_DIR%;%PATH%" >nul
    echo [OK] Directorio agregado al PATH.
    echo     Reabre la terminal para que el cambio surta efecto.
) else (
    echo [OK] %BIN_DIR% ya esta en el PATH.
)

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   Instalacion completada.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo   Usa: juanita
echo   Ayuda: juanita --help
echo.
echo   NOTA: Si el comando no se reconoce, abre una NUEVA terminal.
echo.
pause
