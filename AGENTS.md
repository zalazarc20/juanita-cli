# Juanita CLI — Guía para agentes de IA

Juanita es un CLI en Python que scrapea enlaces de películas y series desde pelisjuanita.com.

## Archivos principales

| Archivo | Propósito |
|---|---|
| `juanita.py` | CLI principal (915 líneas, sin dependencias externas pesadas) |
| `juanita-rofi` | Script Bash para integración con Rofi |
| `skills/juanita-install.md` | Guía de instalación para agentes IA |
| `skills/juanita-rofi.md` | Guía de integración Rofi para agentes IA |

## Skills (opencode)

Las skills de opencode están en `.opencode/skills/juanita-install/SKILL.md` y `.opencode/skills/juanita-rofi/SKILL.md`.

## Stack técnico

- **Lenguaje:** Python 3.7+, solo stdlib + `requests` + `beautifulsoup4` + `pyperclip`
- **Scraping:** `requests.Session` con headers personalizados, `BeautifulSoup` para parseo
- **No usa** Playwright, Selenium, ni navegadores headless
- **Formato de salida:** texto plano o `--json` con `json.dumps`
- **Endpoints scrapeados:** `movies.php`, `movieInfo.php`, `player.php`, `apiSeries.php`, `serieInfo.php`

## Funciones clave

- `parse_movie_card(a_tag)` → extrae `{title, slug, rating, year, image}` de cada resultado
- `parse_servers(soup)` → extrae `{name, url, type, lang, quality, label, download_url}` de servidores
- `cmd_search`, `cmd_series_search` → búsqueda por query
- `cmd_movie_info`, `cmd_series_episode` → detalle + servidores
- `cmd_movie_stream`, `cmd_series_stream` → extrae URL HLS de `player.php`
- `decode_download_url(url)` → decodifica base64 en URLs de descarga

## Campos del JSON de búsqueda

```json
{
  "title": "Avatar: El camino del agua",
  "slug": "avatar-el-camino-del-agua",
  "rating": "7.6",
  "year": "2022",
  "image": "https://image.tmdb.org/t/p/w300//hash.jpg"
}
```

## Rofi script (`juanita-rofi`)

Script Bash que:
1. Toma input del usuario via `rofi -dmenu`
2. Llama a `juanita search --json` y `juanita series-search --json`
3. Muestra resultados combinados en rofi
4. Ofrece acciones: stream (VLC para player.php, navegador para otros), descarga, poster, info
5. Para series: **temporadas → episodios → acciones** (stream, descarga, poster, info, abrir)
6. Extrae HLS directamente con `curl` + regex del player.php seleccionado

## Notas para `juanita-rofi`

- `series-seasons --json` devuelve `{"title": "...", "seasons": [1, 2, 3]}`, NO un array plano
- `series-episodes --json` usa campo `episode` (no `number`)
- El flujo de series es: seasons → episodes → actions (mismas que pelis), sin action menu inicial

Dependencias: `rofi 1.7+`, `jq`, `curl`, `xdg-utils`, `mpv`/`vlc`
