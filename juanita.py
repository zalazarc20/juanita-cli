#!/usr/bin/env python3
"""
Juanita CLI - Obtiene enlaces de películas desde pelisjuanita.com
"""
import re
import sys
import json
import base64
import argparse
from urllib.parse import urlparse, parse_qs
from html import unescape

import requests
from bs4 import BeautifulSoup

BASE = "https://pelisjuanita.com/movies"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer": "https://pelisjuanita.com/",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


# ── helpers ──────────────────────────────────────────────────────

def decode_download_url(url):
    """Decodifica ?get=<base64> de GenerarLinkDescarga"""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    raw = qs.get("get", [None])[0]
    if raw:
        try:
            return base64.b64decode(raw).decode("utf-8")
        except Exception:
            return None
    return None


def parse_movie_card(a_tag):
    """Extrae info de un <a> dentro de .grid-item"""
    slug = a_tag.get("href", "").replace("/movies/pelicula/", "")
    h2 = a_tag.find("h2")
    title = h2.get_text(strip=True) if h2 else ""
    hover = a_tag.find("div", class_="hover-info")
    rating = year = "?"
    if hover:
        l = hover.find("div", class_="left")
        r = hover.find("div", class_="right")
        if l:
            rating = l.get_text(strip=True).replace("★", "").strip()
        if r:
            year = r.get_text(strip=True)
    return {"title": title, "slug": slug, "rating": rating, "year": year}


# ── commands ─────────────────────────────────────────────────────

def cmd_search(query, page=1):
    """Buscar películas"""
    r = SESSION.get(f"{BASE}/movies.php", params={"s": query, "page": page})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='/movies/pelicula/']")
    movies = [parse_movie_card(a) for a in items]
    return movies


def cmd_list(category="estrenos", page=1):
    """Listar películas por categoría"""
    params = {category: ""}
    if page > 1:
        params["page"] = page
    r = SESSION.get(f"{BASE}/movies.php", params=params)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='/movies/pelicula/']")
    movies = [parse_movie_card(a) for a in items]
    return movies


def cmd_info(slug):
    """Obtener info + servidores de una película"""
    r = SESSION.get(f"{BASE}/movieInfo.php", params={"title": slug})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Metadata
    tmdb_tag = soup.find("meta", {"name": "tmdb-id"})
    tmdb_id = tmdb_tag.get("content") if tmdb_tag else None

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else slug

    sinopsis = soup.find("p", class_="sinopsis")
    synopsis = sinopsis.get_text(strip=True) if sinopsis else ""

    # Servidores
    servers = []
    for row in soup.select("div.row-download"):
        url = row.get("data-url") or ""
        idioma = row.get("data-idioma", "")
        tipo = row.get("data-tipo", "")
        onclick = row.get("onclick", "")
        spans = row.find_all("span")
        name = spans[0].get_text(strip=True) if spans else ""
        quality = spans[1].get_text(strip=True) if len(spans) > 1 else ""
        label = spans[2].get_text(strip=True) if len(spans) > 2 else ""

        # download from onclick
        download_url = None
        if tipo == "descarga":
            m = re.search(r"window\.open\('([^']+)'", onclick)
            if m:
                download_url = m.group(1)
            elif url:
                download_url = url
            decoded = decode_download_url(download_url) if download_url else None
            if decoded:
                download_url = decoded

        servers.append({
            "name": name,
            "url": url,
            "type": tipo,
            "lang": idioma,
            "quality": quality,
            "label": label,
            "download_url": download_url,
        })

    # Trailer
    trailer = None
    trailer_div = soup.find("div", class_="video-trailer")
    if trailer_div:
        iframe = trailer_div.find("iframe")
        if iframe:
            trailer = iframe.get("src")

    return {
        "tmdb_id": tmdb_id,
        "title": title,
        "synopsis": synopsis,
        "slug": slug,
        "trailer": trailer,
        "servers": servers,
    }


def cmd_stream(slug):
    """Extrae URL directa del video (HLS) del player propio"""
    # Primero obtenemos el ID del player desde movieInfo
    info = cmd_info(slug)
    player_url = None
    for s in info["servers"]:
        if "player.php" in s["url"]:
            player_url = s["url"]
            break
    if not player_url:
        # fallback: buscar iframe principal
        r = SESSION.get(f"{BASE}/movieInfo.php", params={"title": slug})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        iframe = soup.find("iframe", id="if-video")
        if iframe:
            player_url = iframe.get("src")

    if not player_url:
        eprint("No se encontró player propio")
        return None

    r = SESSION.get(player_url)
    r.raise_for_status()

    # Extraer file: "..." del setup de JWPlayer
    m = re.search(r'file:\s*"([^"]+)"', r.text)
    if m:
        return m.group(1)

    m = re.search(r"file:\s*'([^']+)'", r.text)
    if m:
        return m.group(1)

    eprint("No se pudo extraer la URL del video HLS")
    return None


def cmd_download(slug, lang=None, index=0):
    """Obtener enlace de descarga"""
    info = cmd_info(slug)
    servers = info["servers"]
    downloads = [s for s in servers if s["type"] == "descarga"]
    if lang:
        downloads = [s for s in downloads if s["lang"] == lang]
    if not downloads:
        eprint("No hay enlaces de descarga disponibles")
        return None
    if index >= len(downloads):
        eprint(f"Índice {index} fuera de rango (0-{len(downloads)-1})")
        return None
    return downloads[index]


# ── CLI ──────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(prog="juanita", description="CLI para pelisjuanita.com")
    sub = p.add_subparsers(dest="cmd", required=True)

    # search
    sp = sub.add_parser("search", help="Buscar películas")
    sp.add_argument("query", help="Término de búsqueda")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true", help="Salida JSON")

    # list
    sp = sub.add_parser("list", help="Listar películas")
    sp.add_argument("--category", default="estrenos",
                    choices=["estrenos", "populares", "ultimas-agregadas"])
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    # info
    sp = sub.add_parser("info", help="Info + servidores de una película")
    sp.add_argument("slug", help="Slug de la película (o URL completa)")
    sp.add_argument("--json", action="store_true")

    # stream
    sp = sub.add_parser("stream", help="Obtener URL directa del HLS")
    sp.add_argument("slug", help="Slug de la película")
    sp.add_argument("--json", action="store_true")

    # download
    sp = sub.add_parser("download", help="Obtener enlace de descarga")
    sp.add_argument("slug", help="Slug de la película")
    sp.add_argument("--lang", default=None, choices=["latino", "español", "subtitulada"])
    sp.add_argument("--index", type=int, default=0)
    sp.add_argument("--json", action="store_true")

    args = p.parse_args()

    # Normalizar slug: aceptar URL completa
    if hasattr(args, "slug") and args.slug and args.slug.startswith("http"):
        args.slug = args.slug.rstrip("/").split("/")[-1]

    try:
        if args.cmd == "search":
            movies = cmd_search(args.query, args.page)
            if args.json:
                print(json.dumps(movies, indent=2, ensure_ascii=False))
            else:
                if not movies:
                    print("Sin resultados.")
                    return
                print(f"\n  {'★':<4} {'Año':<6} {'Título':<50} Slug")
                print(f"  {'─'*4} {'─'*6} {'─'*50} {'─'*30}")
                for m in movies:
                    print(f"  {m['rating']:<4} {m['year']:<6} {m['title'][:48]:<50} {m['slug']}")

        elif args.cmd == "list":
            movies = cmd_list(args.category, args.page)
            if args.json:
                print(json.dumps(movies, indent=2, ensure_ascii=False))
            else:
                if not movies:
                    print("Sin resultados.")
                    return
                print(f"\n  {'★':<4} {'Año':<6} {'Título':<50} Slug")
                print(f"  {'─'*4} {'─'*6} {'─'*50} {'─'*30}")
                for m in movies:
                    print(f"  {m['rating']:<4} {m['year']:<6} {m['title'][:48]:<50} {m['slug']}")

        elif args.cmd == "info":
            info = cmd_info(args.slug)
            if args.json:
                print(json.dumps(info, indent=2, ensure_ascii=False))
            else:
                print(f"\n  {info['title']}")
                if info["synopsis"]:
                    print(f"  Sinopsis: {info['synopsis'][:120]}...")
                print(f"  Slug: {info['slug']}")
                if info["trailer"]:
                    print(f"  Trailer: {info['trailer']}")
                print()
                servers = info["servers"]
                by_type = {"stream": [], "descarga": [], "ayuda": []}
                for s in servers:
                    by_type.setdefault(s["type"], []).append(s)
                for stype in ("stream", "descarga"):
                    items = by_type.get(stype, [])
                    if not items:
                        continue
                    print(f"  ── {stype.upper()} ──")
                    for i, s in enumerate(items):
                        url = s["download_url"] or s["url"]
                        print(f"  [{i}] {s['lang']:<12} {s['name']:<14} {s['quality']:<6} {url}")
                    print()

        elif args.cmd == "stream":
            url = cmd_stream(args.slug)
            if args.json:
                print(json.dumps({"url": url}, indent=2))
            else:
                if url:
                    print(f"\n  URL del video (HLS):\n  {url}")
                else:
                    sys.exit(1)

        elif args.cmd == "download":
            dl = cmd_download(args.slug, args.lang, args.index)
            if args.json:
                print(json.dumps(dl, indent=2, ensure_ascii=False))
            else:
                if dl:
                    url = dl["download_url"] or dl["url"]
                    print(f"\n  [{dl['lang']}] {dl['name']} - {dl['quality']}")
                    print(f"  URL: {url}")
                else:
                    sys.exit(1)

    except requests.RequestException as e:
        eprint(f"Error de conexión: {e}")
        sys.exit(1)
    except Exception as e:
        eprint(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
