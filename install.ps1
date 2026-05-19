<#
.SYNOPSIS
    Instala Juanita CLI en Windows.
.DESCRIPTION
    Descarga o instala Juanita CLI desde los archivos locales,
    instala dependencias Python, y agrega el comando al PATH.
.PARAMETER RawUrl
    URL base para descargar los archivos (para instalacion remota).
    Default: https://raw.githubusercontent.com/zalazarc20/juanita-cli/main/
#>

param(
    [string]$RawUrl = "https://raw.githubusercontent.com/zalazarc20/juanita-cli/main/"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ">>> $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "[OK] $msg" -ForegroundColor Green
}

function Write-Err($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
}

# ─── Detectar si estamos en el repo local ───
$localMode = Test-Path "$PSScriptRoot\juanita.py"

if (-not $localMode) {
    Write-Step "Modo remoto: descargando archivos..."
    $tmpDir = "$env:TEMP\juanita-install"
    if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

    $files = @("juanita.py", "requirements.txt")
    foreach ($f in $files) {
        $url = "$RawUrl$f"
        $out = "$tmpDir\$f"
        Write-Step "Descargando $url ..."
        Invoke-WebRequest -Uri $url -OutFile $out
    }

    $scriptPath = "$tmpDir\juanita.py"
    $reqPath = "$tmpDir\requirements.txt"
} else {
    Write-Step "Modo local: usando archivos del repositorio..."
    $scriptPath = "$PSScriptRoot\juanita.py"
    $reqPath = "$PSScriptRoot\requirements.txt"
}

# ─── Verificar Python ───
Write-Step "Verificando Python..."
try {
    $pyVersion = python --version 2>&1
    Write-Ok "Python detectado: $pyVersion"
} catch {
    Write-Err "Python no encontrado. Descargalo desde https://python.org/downloads/"
    Write-Err "Marca 'Add Python to PATH' al instalarlo."
    exit 1
}

# ─── Verificar pip ───
try {
    pip --version 2>&1 | Out-Null
    Write-Ok "pip detectado"
} catch {
    Write-Err "pip no encontrado. Ejecuta: python -m ensurepip --upgrade"
    exit 1
}

# ─── Instalar dependencias ───
Write-Step "Instalando dependencias Python..."
pip install -q -r "$reqPath"
if ($LASTEXITCODE -ne 0) {
    Write-Err "Fallo al instalar dependencias."
    exit 1
}
Write-Ok "Dependencias instaladas"

# ─── Copiar script a AppData ───
$appDir = "$env:LOCALAPPDATA\juanita-cli"
if (-not (Test-Path $appDir)) {
    New-Item -ItemType Directory -Path $appDir -Force | Out-Null
}

Copy-Item -Path $scriptPath -Destination "$appDir\juanita.py" -Force
Write-Ok "Script copiado a $appDir\juanita.py"

# ─── Crear wrapper .cmd en directorio del PATH de usuario ───
$binDir = "$env:USERPROFILE\.juanita-bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
}

$wrapper = "@echo off`npython `"$appDir\juanita.py`" %*"
Set-Content -Path "$binDir\juanita.cmd" -Value $wrapper
Write-Ok "Wrapper creado: $binDir\juanita.cmd"

# ─── Agregar al PATH de usuario ───
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$binDir*") {
    $newPath = "$binDir;$currentPath"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Ok "Directorio $binDir agregado al PATH de usuario (permanente)."
    Write-Host "    Reabre la terminal para que el cambio surta efecto." -ForegroundColor Yellow
} else {
    Write-Ok "$binDir ya estaba en el PATH."
}

# ─── Agregar tambien al PATH de esta sesion ───
$env:Path = "$binDir;$env:Path"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Instalacion completada!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Ejecuta: juanita" -ForegroundColor White
Write-Host "  Ayuda:   juanita --help" -ForegroundColor White
Write-Host ""
Write-Host "  (Si el comando no funciona, abre una NUEVA terminal)" -ForegroundColor Yellow

# ─── Limpieza ───
if ($localMode -eq $false -and (Test-Path $tmpDir)) {
    Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
}
