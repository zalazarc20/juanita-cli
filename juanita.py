#!/usr/bin/env python3
"""
Juanita CLI - Obtiene enlaces de películas desde pelisjuanita.com
"""
import re
import sys
import json
import base64
import argparse
import subprocess
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

# ── ANSI colors ─────────────────────────────────────────────────
C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "gray": "\033[90m",
}

# ── helpers ──────────────────────────────────────────────────────

def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


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
    slug = a_tag.get("href", "").rstrip("/").split("/")[-1]
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


# ── API commands ─────────────────────────────────────────────────

def cmd_search(query, page=1):
    """Buscar películas"""
    r = SESSION.get(f"{BASE}/movies.php", params={"s": query, "page": page})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='/movies/pelicula/']")
    return [parse_movie_card(a) for a in items]


def cmd_list(category="estrenos", page=1):
    """Listar películas por categoría"""
    params = {category: ""}
    if page > 1:
        params["page"] = page
    r = SESSION.get(f"{BASE}/movies.php", params=params)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='/movies/pelicula/']")
    return [parse_movie_card(a) for a in items]


def cmd_info(slug):
    """Obtener info + servidores de una película"""
    r = SESSION.get(f"{BASE}/movieInfo.php", params={"title": slug})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tmdb_tag = soup.find("meta", {"name": "tmdb-id"})
    tmdb_id = tmdb_tag.get("content") if tmdb_tag else None

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else slug

    sinopsis = soup.find("p", class_="sinopsis")
    synopsis = sinopsis.get_text(strip=True) if sinopsis else ""

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

    return {
        "tmdb_id": tmdb_id,
        "title": title,
        "synopsis": synopsis,
        "slug": slug,
        "servers": servers,
    }


def cmd_stream(slug):
    """Extrae URL directa del video (HLS) del player propio"""
    info = cmd_info(slug)
    player_url = None
    for s in info["servers"]:
        if "player.php" in s["url"]:
            player_url = s["url"]
            break
    if not player_url:
        r = SESSION.get(f"{BASE}/movieInfo.php", params={"title": slug})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        iframe = soup.find("iframe", id="if-video")
        if iframe:
            player_url = iframe.get("src")

    if not player_url:
        return None

    r = SESSION.get(player_url)
    r.raise_for_status()

    m = re.search(r'file:\s*"([^"]+)"', r.text)
    if m:
        return m.group(1)
    m = re.search(r"file:\s*'([^']+)'", r.text)
    if m:
        return m.group(1)
    return None


def cmd_download(slug, lang=None, index=0):
    """Obtener enlace de descarga"""
    info = cmd_info(slug)
    servers = info["servers"]
    downloads = [s for s in servers if s["type"] == "descarga"]
    if lang:
        downloads = [s for s in downloads if s["lang"] == lang]
    if not downloads or index >= len(downloads):
        return None
    return downloads[index]


# ── Interactive menu ─────────────────────────────────────────────

def esc():
    print(f"{C['reset']}", end="", flush=True)


def clear():
    print("\033[2J\033[H", end="")


def banner():
    clear()
    print(f"""  {C['bold']}{C['cyan']}╔══════════════════════════════════════════╗
  ║       🎬  JUANITA CLI  v2              ║
  ║   Encuentra películas en la web        ║
  ╚══════════════════════════════════════════╝{C['reset']}
""")


def press_enter():
    input(f"\n  {C['dim']}Presiona Enter para continuar...{C['reset']}")


def show_movies(movies, page=1, total_pages=None):
    """Muestra lista de películas numeradas"""
    if not movies:
        print(f"\n  {C['yellow']}Sin resultados.{C['reset']}")
        return

    print(f"\n  {C['bold']}{'#':<4} {'★':<5} {'Año':<6} {'Título'}{C['reset']}")
    print(f"  {C['gray']}{'─'*4} {'─'*5} {'─'*6} {'─'*60}{C['reset']}")
    for i, m in enumerate(movies):
        print(f"  {C['cyan']}{i+1:<4}{C['reset']} {m['rating']:<5} {m['year']:<6} {m['title'][:58]}")
    if total_pages:
        print(f"\n  {C['dim']}Página {page} de {total_pages}{C['reset']}")


def menu_select_movie(movies, page=1):
    """Menú para seleccionar una película de la lista"""
    while True:
        print(f"\n  {C['green']}[N]{C['reset']} Seleccionar película (1-{len(movies)})")
        print(f"  {C['yellow']}[P]{C['reset']} Página anterior")
        print(f"  {C['yellow']}[S]{C['reset']} Página siguiente")
        print(f"  {C['red']}[B]{C['reset']} Volver atrás")
        print(f"  {C['red']}[Q]{C['reset']} Salir")
        choice = input(f"\n  {C['bold']}➜{C['reset']} ").strip().lower()

        if choice == "q":
            print(f"\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)
        elif choice == "b":
            return None
        elif choice == "p":
            return "prev"
        elif choice == "s":
            return "next"
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(movies):
                return movies[idx]
            print(f"  {C['red']}Número inválido.{C['reset']}")
        else:
            print(f"  {C['red']}Opción inválida.{C['reset']}")


def show_movie_detail(slug):
    """Muestra info detallada y enlaces de una película"""
    info = cmd_info(slug)
    hls_url = cmd_stream(slug)

    clear()
    print(f"""
  {C['bold']}{C['cyan']}╔══════════════════════════════════════════╗
  ║  {info['title'][:42]:<42} ║
  ╚══════════════════════════════════════════╝{C['reset']}
""")
    if info["synopsis"]:
        print(f"  {C['dim']}{info['synopsis'][:200]}{C['reset']}\n")

    servers = info["servers"]
    streams = [s for s in servers if s["type"] == "stream"]
    downloads = [s for s in servers if s["type"] == "descarga"]

    if streams:
        print(f"  {C['bold']}{C['green']}📺  STREAMING{C['reset']}")
        print(f"  {C['gray']}{'─'*65}{C['reset']}")
        for i, s in enumerate(streams):
            url = s["url"]
            print(f"  {C['cyan']}[{i+1}]{C['reset']} {s['lang']:<10} {C['bold']}{s['name']:<12}{C['reset']} {s['quality']:<5}")
            print(f"       {C['dim']}{url}{C['reset']}")
        print()

    if downloads:
        print(f"  {C['bold']}{C['yellow']}⬇  DESCARGA{C['reset']}")
        print(f"  {C['gray']}{'─'*65}{C['reset']}")
        for i, s in enumerate(downloads):
            url = s["download_url"] or s["url"]
            print(f"  {C['cyan']}[{i+1}]{C['reset']} {s['lang']:<10} {C['bold']}{s['name']:<12}{C['reset']} {s['quality']:<5}")
            print(f"       {C['dim']}{url}{C['reset']}")
        print()

    if hls_url:
        print(f"  {C['bold']}{C['magenta']}🎬  ENLACE DIRECTO HLS (VLC){C['reset']}")
        print(f"  {C['gray']}{'─'*65}{C['reset']}")
        print(f"       {C['dim']}{hls_url}{C['reset']}")
        print(f"  {C['green']}  [V]{C['reset']} Abrir en VLC")
        print(f"  {C['yellow']}  [C]{C['reset']} Copiar al portapapeles")
        print()

    print(f"  {C['bold']}{C['cyan']}──  Opciones ──{C['reset']}")
    print(f"  {C['green']}[1-{len(streams)}]{C['reset']} Abrir enlace de streaming en navegador")
    if downloads:
        print(f"  {C['yellow']}[D1-D{len(downloads)}]{C['reset']} Abrir enlace de descarga en navegador")
    if hls_url:
        print(f"  {C['magenta']}[V]{C['reset']} Abrir en VLC")
        print(f"  {C['yellow']}[C]{C['reset']} Copiar enlace directo")
    print(f"  {C['red']}[B]{C['reset']} Volver")
    print(f"  {C['red']}[Q]{C['reset']} Salir")

    while True:
        choice = input(f"\n  {C['bold']}➜{C['reset']} ").strip().lower()

        if choice == "q":
            print(f"\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)
        elif choice == "b":
            return
        elif choice == "v" and hls_url:
            try:
                subprocess.Popen(["vlc", hls_url],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                print(f"  {C['green']}Abriendo VLC...{C['reset']}")
            except FileNotFoundError:
                print(f"  {C['red']}VLC no encontrado. Instalalo o abre el enlace manualmente.{C['reset']}")
            press_enter()
        elif choice == "c" and hls_url:
            try:
                import pyperclip
                pyperclip.copy(hls_url)
                print(f"  {C['green']}Enlace copiado al portapapeles.{C['reset']}")
            except ImportError:
                # fallback: mostrar comando
                print(f"\n  Copia este comando:")
                print(f"  echo '{hls_url}' | xclip -selection clipboard")
                print(f"  # o manualmente")
            press_enter()
        elif choice.startswith("d"):
            num = choice[1:]
            if num.isdigit() and downloads:
                idx = int(num) - 1
                if 0 <= idx < len(downloads):
                    url = downloads[idx]["download_url"] or downloads[idx]["url"]
                    import webbrowser
                    webbrowser.open(url)
                    print(f"  {C['green']}Abriendo en navegador...{C['reset']}")
                    press_enter()
                    return
            print(f"  {C['red']}Opción inválida.{C['reset']}")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(streams):
                import webbrowser
                webbrowser.open(streams[idx]["url"])
                print(f"  {C['green']}Abriendo en navegador...{C['reset']}")
                press_enter()
                return
            print(f"  {C['red']}Número inválido.{C['reset']}")
        else:
            print(f"  {C['red']}Opción inválida.{C['reset']}")


def main_menu():
    """Menú principal interactivo"""
    while True:
        banner()
        print(f"  {C['bold']}Menú Principal{C['reset']}")
        print(f"  {C['gray']}{'─'*40}{C['reset']}")
        print(f"  {C['cyan']}[1]{C['reset']} 🔍  Buscar película")
        print(f"  {C['cyan']}[2]{C['reset']} 📋  Ver estrenos")
        print(f"  {C['cyan']}[3]{C['reset']} 🔥  Ver populares")
        print(f"  {C['cyan']}[4]{C['reset']} ✨  Ver últimas agregadas")
        print(f"  {C['red']}[5]{C['reset']} 🚪  Salir")
        print()

        choice = input(f"  {C['bold']}➜{C['reset']} ").strip()

        if choice == "5" or choice.lower() == "q":
            print(f"\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)

        category = None
        if choice == "1":
            query = input(f"\n  {C['bold']}Nombre de la película: {C['reset']}").strip()
            if not query:
                continue
            try:
                movies = cmd_search(query)
            except Exception as e:
                print(f"  {C['red']}Error: {e}{C['reset']}")
                press_enter()
                continue
            clear()
            print(f"\n  {C['bold']}Resultados para: {C['yellow']}{query}{C['reset']}")
            show_movies(movies)
            if not movies:
                press_enter()
                continue

            while True:
                sel = menu_select_movie(movies)
                if sel is None:
                    break
                elif sel == "prev" or sel == "next":
                    print(f"  {C['yellow']}Solo hay una página.{C['reset']}")
                    continue
                else:
                    show_movie_detail(sel["slug"])

        elif choice in ("2", "3", "4"):
            cat_map = {"2": "estrenos", "3": "populares", "4": "ultimas-agregadas"}
            category = cat_map[choice]
            page = 1
            while True:
                try:
                    movies = cmd_list(category, page)
                except Exception as e:
                    print(f"  {C['red']}Error: {e}{C['reset']}")
                    press_enter()
                    break
                clear()
                print(f"\n  {C['bold']}{category.replace('-', ' ').title()}{C['reset']}")
                show_movies(movies)
                if not movies:
                    press_enter()
                    break

                sel = menu_select_movie(movies, page)
                if sel is None:
                    break
                elif sel == "prev":
                    if page > 1:
                        page -= 1
                    else:
                        print(f"  {C['yellow']}Ya estás en la primera página.{C['reset']}")
                elif sel == "next":
                    page += 1
                else:
                    show_movie_detail(sel["slug"])

        else:
            print(f"  {C['red']}Opción inválida.{C['reset']}")
            press_enter()


# ── CLI mode ─────────────────────────────────────────────────────

def cli_mode():
    p = argparse.ArgumentParser(prog="juanita", description="CLI para pelisjuanita.com")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("search", help="Buscar películas")
    sp.add_argument("query", help="Término de búsqueda")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("list", help="Listar películas")
    sp.add_argument("--category", default="estrenos",
                    choices=["estrenos", "populares", "ultimas-agregadas"])
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("info", help="Info + servidores de una película")
    sp.add_argument("slug", help="Slug de la película (o URL completa)")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("stream", help="Obtener URL directa del HLS")
    sp.add_argument("slug", help="Slug de la película")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("download", help="Obtener enlace de descarga")
    sp.add_argument("slug", help="Slug de la película")
    sp.add_argument("--lang", default=None, choices=["latino", "español", "subtitulada"])
    sp.add_argument("--index", type=int, default=0)
    sp.add_argument("--json", action="store_true")

    args = p.parse_args()

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


# ── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_mode()
    else:
        try:
            main_menu()
        except KeyboardInterrupt:
            print(f"\n\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)
