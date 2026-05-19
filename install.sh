#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
SCRIPT_SRC="$(dirname "$0")/juanita.py"
CMD_NAME="juanita"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━ Juanita CLI — Instalación ━━━${NC}"

# Detectar OS
OS="$(uname -s)"
case "$OS" in
  Linux)  BIN_DIR="$INSTALL_DIR" ;;
  Darwin) BIN_DIR="$INSTALL_DIR" ;;
  MINGW*|MSYS*|CYGWIN*)
    BIN_DIR="${INSTALL_DIR}"
    SCRIPT_SRC="$(cd "$(dirname "$0")" && pwd)/juanita.py"
    # En Windows se crea un .cmd wrapper
    CMD_PATH="$BIN_DIR/$CMD_NAME.cmd"
    echo -e "${CYAN}► Windows detectado — creando $CMD_PATH${NC}"
    mkdir -p "$BIN_DIR"
    cat > "$CMD_PATH" <<- WRAP
@echo off
python3 "$(cygpath -w "$SCRIPT_SRC" 2>/dev/null || echo "$SCRIPT_SRC")" %*
WRAP
    echo -e "${GREEN}✓ Instalado en $CMD_PATH${NC}"
    echo -e "${CYAN}  Asegúrate de que $BIN_DIR esté en tu PATH.${NC}"
    exit 0
    ;;
  *)
    echo -e "${RED}OS no soportado: $OS${NC}"
    echo "  Instalación manual: python3 juanita.py"
    exit 1
    ;;
esac

# Linux / macOS
mkdir -p "$BIN_DIR"
TARGET="$BIN_DIR/$CMD_NAME"

# Copiar el script
install -m 755 "$SCRIPT_SRC" "$TARGET"

# Verificar dependencias
echo -e "${CYAN}► Verificando dependencias...${NC}"
    python3 -c "import requests; import bs4" 2>/dev/null || {
  echo -e "${CYAN}► Instalando requests, beautifulsoup4 y pyperclip...${NC}"
  pip3 install --quiet requests beautifulsoup4 pyperclip
}

echo -e "${GREEN}✓ Instalado en $TARGET${NC}"
echo -e "${CYAN}  Ejecutá: juanita${NC}"
echo -e "${CYAN}  Ayuda:   juanita --help${NC}"
