# Juanita CLI

CLI en Python para obtener enlaces de películas y series desde [pelisjuanita.com](https://pelisjuanita.com).

Solo usa `requests` + `BeautifulSoup` — sin navegadores, sin Playwright, sin Selenium.

## Instalación

### Linux / macOS

```bash
# Opción 1 — Script automático
bash install.sh

# Opción 2 — Manual
pip install requests beautifulsoup4 pyperclip
python3 juanita.py

# Opción 3 — Un solo comando (sin clonar el repo)
bash <(curl -s https://raw.githubusercontent.com/zalazarc20/juanita-cli/main/install.sh)
```

> El script `install.sh` copia `juanita.py` a `/usr/local/bin/juanita` e instala las dependencias.  
> El wrapper queda disponible como el comando `juanita` desde cualquier terminal.

### Windows

#### Requisitos

- [Python 3.7+](https://python.org/downloads/) (marcar **"Add Python to PATH"** durante la instalación)

#### Opción 1 — Script PowerShell (recomendado)

Abrí **PowerShell como administrador** y ejecutá:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/zalazarc20/juanita-cli/main/install.ps1'))
```

Esto descarga e instala todo automáticamente (dependencias + wrapper + PATH).

#### Opción 2 — Batch (cmd)

Si clonaste el repo, ejecutá:

```cmd
install.bat
```

#### Opción 3 — PowerShell one-liner (sin clonar, sin políticas de ejecución)

```powershell
powershell -c "iwr https://raw.githubusercontent.com/zalazarc20/juanita-cli/main/install.ps1 -OutFile $env:TEMP\install-juanita.ps1; & $env:TEMP\install-juanita.ps1"
```

#### Opción 4 — Manual

```cmd
pip install requests beautifulsoup4 pyperclip
python juanita.py
```

## Modo interactivo (menú)

Sin argumentos:

```bash
juanita
```

Menú principal con películas y series, navegación numérica, selección de episodios por temporada, y apertura directa en navegador o VLC.

## Modo CLI

```bash
juanita <comando> [opciones]
```

### Películas

| Comando | Descripción |
|---|---|
| `search <query>` | Buscar películas |
| `list --category estrenos` | Listar por categoría |
| `info <slug>` | Info + servidores |
| `stream <slug>` | URL directa HLS |
| `download <slug>` | Link de descarga |

```bash
juanita search "punisher"
juanita search "matrix" --json
juanita list --category populares --page 2
juanita info the-punisher-la-ultima-muerte
juanita info "https://pelisjuanita.com/movies/pelicula/the-punisher-la-ultima-muerte"
juanita stream the-punisher-la-ultima-muerte
juanita download the-punisher-la-ultima-muerte --lang latino
```

### Series

| Comando | Descripción |
|---|---|
| `series-search <query>` | Buscar series |
| `series-list --category populares` | Listar series |
| `series-seasons <slug>` | Ver temporadas |
| `series-episodes <slug> <season>` | Ver episodios de una temporada |
| `series-episode <slug> <season> <ep>` | Info + servidores de un episodio |

```bash
juanita series-search "breaking"
juanita series-list --category estrenos
juanita series-seasons breaking-bad
juanita series-episodes breaking-bad 1
juanita series-episode breaking-bad 1 1
juanita series-episode breaking-bad 1 1 --json
```

Todos aceptan `--json` para output estructurado.

## Endpoints (referencia)

### Películas

| Endpoint | Descripción |
|---|---|
| `GET /movies/movies.php?s=<query>` | Búsqueda |
| `GET /movies/movies.php?estrenos=&page=N` | Listar + paginación |
| `GET /movies/movieInfo.php?title=<slug>` | Detalle + servidores |
| `GET /movies/player.php?id=<id>` | Player JWPlayer (HLS) |

### Series

| Endpoint | Descripción |
|---|---|
| `GET /series/apiSeries.php?s=<query>` | Búsqueda de series |
| `GET /series/apiSeries.php?populares=&page=N` | Listar + paginación |
| `GET /series/serieInfo.php?nombreSerie=X&nroTemporada=N&nroEpisodio=M` | Detalle episodio + servidores |
| `GET /series/serieInfo.php?nombreSerie=X&temporada=N&snum=N&enum=N` | Episodios de una temporada |
