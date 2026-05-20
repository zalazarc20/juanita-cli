# Juanita CLI — Instalación

Juanita es un CLI en Python para scrappear enlaces de películas y series desde pelisjuanita.com. Usa `requests` + `BeautifulSoup`.

## Requisitos

- Python 3.7+
- pip

## Instalación

```bash
# Opción 1 — Script automático
git clone https://github.com/zalazarc20/juanita-cli.git
cd juanita-cli
bash install.sh

# Opción 2 — Manual
pip install requests beautifulsoup4 pyperclip
python3 juanita.py

# Opción 3 — Un solo comando
bash <(curl -s https://raw.githubusercontent.com/zalazarc20/juanita-cli/main/install.sh)
```

El script `install.sh` copia `juanita.py` a `/usr/local/bin/juanita` e instala las dependencias. El comando `juanita` queda disponible globalmente.

## Uso básico

```bash
juanita                       # Modo interactivo (menú)
juanita search "avatar"       # Buscar películas
juanita search "avatar" --json | jq '.[] | .title, .image'  # Con poster TMDB
juanita info avatar           # Info + servidores
juanita stream avatar         # URL directa HLS
juanita download avatar       # Link de descarga

# Series
juanita series-search "breaking"
juanita series-seasons breaking-bad
juanita series-episodes breaking-bad 1
juanita series-episode breaking-bad 1 1
```

## Salida JSON

Todos los comandos aceptan `--json`. Desde la última versión, los resultados de búsqueda incluyen `image` (URL del poster TMDB):

```json
{
  "title": "Avatar: El camino del agua",
  "slug": "avatar-el-camino-del-agua",
  "rating": "7.6",
  "year": "2022",
  "image": "https://image.tmdb.org/t/p/w300//ckeTumMS4G31UQ9NNkmtW2QhfMF.jpg"
}
```

## Estructura del proyecto

```
juanita-cli/
├── juanita.py          # CLI principal (todo el scraping)
├── juanita-rofi        # Script de integración con Rofi
├── install.sh          # Instalador Linux/macOS
├── install.bat         # Instalador Windows (batch)
├── install.ps1         # Instalador Windows (PowerShell)
├── requirements.txt    # Dependencias Python
├── README.md           # Documentación
└── skills/             # Skills para agentes de IA
```

## Modo interactivo

Sin argumentos abre un menú navegable con películas y series, selección de episodios por temporada, y apertura en navegador/VLC.
