---
name: juanita-install
description: Use when the user asks about installing, setting up, or configuring Juanita CLI. Covers Python dependencies, install.sh, PATH setup, and basic usage of the juanita command.
---

# Juanita CLI — Instalación

Juanita es un CLI en Python para scrappear enlaces de películas y series desde pelisjuanita.com.

## Instalación

```bash
git clone https://github.com/zalazarc20/juanita-cli.git
cd juanita-cli
bash install.sh   # copia a /usr/local/bin/juanita
```

O manual:

```bash
pip install requests beautifulsoup4 pyperclip
# luego ejecutar directo: python3 juanita.py
```

## Comandos básicos

| Comando | Descripción |
|---|---|
| `juanita` | Menú interactivo |
| `juanita search <query>` | Buscar películas |
| `juanita info <slug>` | Info + servidores |
| `juanita stream <slug>` | URL HLS directa |
| `juanita download <slug>` | Link de descarga |
| `juanita series-search <query>` | Buscar series |
| `juanita series-seasons <slug>` | Temporadas |
| `juanita series-episodes <slug> <season>` | Episodios |
| `juanita series-episode <slug> <season> <ep>` | Servidores de episodio |
| `juanita series-stream <slug> <season> <ep>` | HLS de episodio |

Todos aceptan `--json`. La salida incluye `image` (URL del poster TMDB).

## Estructura del proyecto

```
juanita-cli/
├── juanita.py          # CLI principal
├── juanita-rofi        # Integración con Rofi
├── install.sh          # Instalador Linux/macOS
├── install.bat / .ps1  # Instaladores Windows
├── requirements.txt    # Dependencias
├── README.md
├── skills/             # Skills para IA (markdown genérico)
└── .opencode/skills/   # Skills para opencode
```
