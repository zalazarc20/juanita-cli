# Juanita CLI

CLI en Python para obtener enlaces de películas desde [pelisjuanita.com](https://pelisjuanita.com/movies/estrenos/).

Solo usa `requests` + `BeautifulSoup` — sin navegadores, sin Playwright, sin Selenium.

## Requisitos

```bash
pip install requests beautifulsoup4
```

## Uso

```bash
python3 juanita.py <comando> [opciones]
```

### `search` — Buscar películas

```bash
python3 juanita.py search "punisher"
python3 juanita.py search "matrix" --page 2
python3 juanita.py search "inception" --json
```

### `list` — Listar películas por categoría

```bash
python3 juanita.py list
python3 juanita.py list --category populares
python3 juanita.py list --category ultimas-agregadas --page 3
python3 juanita.py list --json
```

Categorías disponibles: `estrenos` (default), `populares`, `ultimas-agregadas`.

### `info` — Info completa + servidores de una película

```bash
python3 juanita.py info the-punisher-la-ultima-muerte
python3 juanita.py info "https://pelisjuanita.com/movies/pelicula/the-punisher-la-ultima-muerte"
python3 juanita.py info the-punisher-la-ultima-muerte --json
```

Muestra:
- Título, sinopsis, slug
- **Streaming:** Pelisjuanita (propio), Player4me, Seek, Dood, Byse, Voe, Vidsrc
- **Descarga:** Dood, Byse, Voe, 1fichier, Player4me, Seek

### `stream` — URL directa del video (HLS)

Extrae la URL `.m3u8` del player propio de Pelisjuanita (JWPlayer).

```bash
python3 juanita.py stream the-punisher-la-ultima-muerte
python3 juanita.py stream the-punisher-la-ultima-muerte --json
```

> **Nota:** el token `hdnts` expira, la URL tiene tiempo de vida limitado.

### `download` — Enlace de descarga directa

```bash
python3 juanita.py download the-punisher-la-ultima-muerte
python3 juanita.py download the-punisher-la-ultima-muerte --lang latino
python3 juanita.py download the-punisher-la-ultima-muerte --lang español --index 1
python3 juanita.py download the-punisher-la-ultima-muerte --json
```

Idiomas: `latino`, `español`, `subtitulada`.

## Salida JSON

Todos los comandos aceptan `--json` para output estructurado.

```bash
python3 juanita.py search "avengers" --json | jq '.'
python3 juanita.py info avengers-endgame --json | jq '.servers[] | select(.type=="stream")'
```

## Endpoints (para referencia)

| Endpoint | Descripción |
|---|---|
| `GET /movies/movies.php?s=<query>` | Búsqueda de películas |
| `GET /movies/movies.php?estrenos=&page=N` | Listar por categoría + paginación |
| `GET /movies/movieInfo.php?title=<slug>` | Detalle de película + servidores |
| `GET /movies/player.php?id=<id>` | Player JWPlayer con HLS embedido |
