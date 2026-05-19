#!/usr/bin/env python3
"""
Juanita CLI - Obtiene enlaces de películas y series desde pelisjuanita.com
"""
import re
import sys
import json
import base64
import argparse
import subprocess
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

BASE = "https://pelisjuanita.com"
MOVIES_BASE = f"{BASE}/movies"
SERIES_BASE = f"{BASE}/series"
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

def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


# ── helpers ──────────────────────────────────────────────────────

def decode_download_url(url):
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


def parse_servers(soup):
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
    return servers


# ── Películas ────────────────────────────────────────────────────

def cmd_search(query, page=1):
    r = SESSION.get(f"{MOVIES_BASE}/movies.php", params={"s": query, "page": page})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='/movies/pelicula/']")
    return [parse_movie_card(a) for a in items]


def cmd_list(category="estrenos", page=1):
    params = {category: ""}
    if page > 1:
        params["page"] = page
    r = SESSION.get(f"{MOVIES_BASE}/movies.php", params=params)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='/movies/pelicula/']")
    return [parse_movie_card(a) for a in items]


def cmd_movie_info(slug):
    r = SESSION.get(f"{MOVIES_BASE}/movieInfo.php", params={"title": slug})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tmdb_tag = soup.find("meta", {"name": "tmdb-id"})
    tmdb_id = tmdb_tag.get("content") if tmdb_tag else None
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else slug
    sinopsis = soup.find("p", class_="sinopsis")
    synopsis = sinopsis.get_text(strip=True) if sinopsis else ""
    return {
        "tmdb_id": tmdb_id,
        "title": title,
        "synopsis": synopsis,
        "slug": slug,
        "type": "movie",
        "servers": parse_servers(soup),
    }


def cmd_movie_stream(slug):
    info = cmd_movie_info(slug)
    player_url = None
    for s in info["servers"]:
        if "player.php" in s["url"]:
            player_url = s["url"]
            break
    if not player_url:
        r = SESSION.get(f"{MOVIES_BASE}/movieInfo.php", params={"title": slug})
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


def cmd_movie_download(slug, lang=None, index=0):
    info = cmd_movie_info(slug)
    downloads = [s for s in info["servers"] if s["type"] == "descarga"]
    if lang:
        downloads = [s for s in downloads if s["lang"] == lang]
    if not downloads or index >= len(downloads):
        return None
    return downloads[index]


# ── Series ───────────────────────────────────────────────────────

def cmd_series_search(query, page=1):
    r = SESSION.get(f"{SERIES_BASE}/apiSeries.php", params={"s": query, "page": page})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='ver-serie/']")
    return [parse_movie_card(a) for a in items]


def cmd_series_list(category="populares", page=1):
    params = {category: ""}
    if page > 1:
        params["page"] = page
    r = SESSION.get(f"{SERIES_BASE}/apiSeries.php", params=params)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("div.grid-item a[href^='ver-serie/']")
    return [parse_movie_card(a) for a in items]


def cmd_series_episode(slug, season, episode):
    """Obtener info y servidores de un episodio específico"""
    r = SESSION.get(f"{SERIES_BASE}/serieInfo.php", params={
        "nombreSerie": slug,
        "nroTemporada": season,
        "nroEpisodio": episode,
    })
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tmdb_tag = soup.find("meta", {"name": "tmdb-id"})
    tmdb_id = tmdb_tag.get("content") if tmdb_tag else None
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else slug
    sinopsis = soup.find("p", class_="sinopsis")
    synopsis = sinopsis.get_text(strip=True) if sinopsis else ""

    # Episode info (e.g. "01x01 Piloto • 20/01/2008")
    ep_label = ""
    ep_p = soup.find("p", string=re.compile(r"\[\d+x\d+\]"))
    if ep_p:
        ep_label = ep_p.get_text(strip=True)

    # Seasons list from dropdown
    seasons = []
    dropdown = soup.find("div", id="temporadasDropdown")
    if dropdown:
        for item in dropdown.select("div.server-item"):
            text = item.get_text(strip=True)
            m = re.search(r"Temporada\s+(\d+)", text)
            if m:
                seasons.append(int(m.group(1)))

    # Previous/next episode navigation
    nav_prev = nav_next = None
    for a in soup.select("a.comandos"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if "Anterior" in text:
            nav_prev = href
        elif "Siguiente" in text:
            nav_next = href

    # Extract player.php URL (for series that have direct HLS)
    player_url = None
    for s in parse_servers(soup):
        if "player.php" in s["url"]:
            player_url = s["url"]
            break
    if not player_url:
        iframe = soup.find("iframe", id="if-video")
        if iframe:
            player_url = iframe.get("src")

    return {
        "tmdb_id": tmdb_id,
        "title": title,
        "synopsis": synopsis,
        "slug": slug,
        "season": season,
        "episode": episode,
        "episode_label": ep_label,
        "type": "episode",
        "seasons": seasons,
        "nav_prev": nav_prev,
        "nav_next": nav_next,
        "servers": parse_servers(soup),
        "player_url": player_url,
    }


def cmd_series_stream(slug, season, episode):
    """Extraer URL directa HLS de un episodio (si tiene player.php)"""
    info = cmd_series_episode(slug, season, episode)
    if not info["player_url"]:
        return None
    r = SESSION.get(info["player_url"])
    r.raise_for_status()
    m = re.search(r'file:\s*"([^"]+)"', r.text)
    if m:
        return m.group(1)
    m = re.search(r"file:\s*'([^']+)'", r.text)
    if m:
        return m.group(1)
    return None


def cmd_series_season_episodes(slug, season):
    """Obtener lista de episodios de una temporada"""
    # First get the episode page to extract snum/enum
    r = SESSION.get(f"{SERIES_BASE}/serieInfo.php", params={
        "nombreSerie": slug,
        "nroTemporada": season,
        "nroEpisodio": 1,
    })
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    snum_tag = soup.find("meta", {"name": "snum"})
    enum_tag = soup.find("meta", {"name": "enum"})
    snum = snum_tag.get("content") if snum_tag else season
    enum = enum_tag.get("content") if enum_tag else "1"

    # Now get the episode list
    r2 = SESSION.get(f"{SERIES_BASE}/serieInfo.php", params={
        "nombreSerie": slug,
        "temporada": season,
        "snum": snum,
        "enum": enum,
    })
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, "html.parser")

    episodes = []
    for item in soup2.select("a.episodio-item"):
        href = item.get("href", "")
        h2 = item.find("h2", class_="list-title")
        ep_title = h2.get_text(strip=True) if h2 else ""
        ep_title = re.sub(r"^\[?\d+x\d+\]?\s*", "", ep_title).strip()
        ep_match = re.search(r"(\d+)x(\d+)", href)
        if ep_match:
            episodes.append({
                "season": int(ep_match.group(1)),
                "episode": int(ep_match.group(2)),
                "title": ep_title,
                "href": href,
            })
    return episodes


# ── Interactive menu ─────────────────────────────────────────────

def esc():
    print(f"{C['reset']}", end="", flush=True)


def clear():
    print("\033[2J\033[H", end="")


def banner():
    clear()
    print(f"""  {C['bold']}{C['cyan']}╔══════════════════════════════════════════╗
  ║       🎬  JUANITA CLI  v3              ║
  ║   Películas y Series desde la web      ║
  ╚══════════════════════════════════════════╝{C['reset']}
""")


def press_enter():
    input(f"\n  {C['dim']}Presiona Enter para continuar...{C['reset']}")


def show_movies(movies):
    if not movies:
        print(f"\n  {C['yellow']}Sin resultados.{C['reset']}")
        return
    print(f"\n  {C['bold']}{'#':<4} {'★':<5} {'Año':<6} {'Título'}{C['reset']}")
    print(f"  {C['gray']}{'─'*4} {'─'*5} {'─'*6} {'─'*60}{C['reset']}")
    for i, m in enumerate(movies):
        print(f"  {C['cyan']}{i+1:<4}{C['reset']} {m['rating']:<5} {m['year']:<6} {m['title'][:58]}")


def menu_nav():
    print(f"\n  {C['green']}[N]{C['reset']}  Seleccionar por número (1, 2, ...)")
    print(f"  {C['red']}[B]{C['reset']}  Volver atrás")
    print(f"  {C['red']}[Q]{C['reset']}  Salir")
    while True:
        choice = input(f"\n  {C['bold']}➜{C['reset']} ").strip().lower()
        if choice == "q":
            print(f"\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)
        elif choice == "b":
            return None
        elif choice.isdigit():
            return int(choice) - 1
        print(f"  {C['red']}Opción inválida.{C['reset']}")


def show_servers_dialog(info, hls_url=None):
    clear()
    print(f"""
  {C['bold']}{C['cyan']}╔══════════════════════════════════════════╗
  ║  {info['title'][:42]:<42} ║
  ╚══════════════════════════════════════════╝{C['reset']}
""")
    if info.get("episode_label"):
        print(f"  {C['yellow']}{info['episode_label']}{C['reset']}\n")
    if info["synopsis"]:
        print(f"  {C['dim']}{info['synopsis'][:200]}{C['reset']}\n")

    servers = info["servers"]
    streams = [s for s in servers if s["type"] == "stream"]
    downloads = [s for s in servers if s["type"] == "descarga"]

    if streams:
        print(f"  {C['bold']}{C['green']}📺  STREAMING{C['reset']}")
        print(f"  {C['gray']}{'─'*65}{C['reset']}")
        for i, s in enumerate(streams):
            print(f"  {C['cyan']}[{i+1}]{C['reset']} {s['lang']:<10} {C['bold']}{s['name']:<12}{C['reset']} {s['quality']:<5}")
            print(f"       {C['dim']}{s['url']}{C['reset']}")
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
    print(f"  {C['green']}[1-{len(streams)}]{C['reset']} Abrir streaming en navegador")
    if downloads:
        print(f"  {C['yellow']}[D1-D{len(downloads)}]{C['reset']} Abrir descarga en navegador")
    if hls_url:
        print(f"  {C['magenta']}[V]{C['reset']} Abrir en VLC")
        print(f"  {C['yellow']}[C]{C['reset']} Copiar enlace directo")
    if info.get("nav_prev"):
        print(f"  {C['blue']}[P]{C['reset']} Episodio anterior")
    if info.get("nav_next"):
        print(f"  {C['blue']}[N]{C['reset']} Episodio siguiente")
    print(f"  {C['red']}[B]{C['reset']} Volver")
    print(f"  {C['red']}[Q]{C['reset']} Salir")

    while True:
        choice = input(f"\n  {C['bold']}➜{C['reset']} ").strip().lower()

        if choice == "q":
            print(f"\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)
        elif choice == "b":
            return None
        elif choice == "v" and hls_url:
            try:
                subprocess.Popen(["vlc", hls_url],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  {C['green']}Abriendo VLC...{C['reset']}")
            except FileNotFoundError:
                print(f"  {C['red']}VLC no encontrado.{C['reset']}")
            press_enter()
        elif choice == "c" and hls_url:
            try:
                import pyperclip
                pyperclip.copy(hls_url)
                print(f"  {C['green']}Enlace copiado.{C['reset']}")
            except ImportError:
                print(f"\n  Copia este enlace:\n  {hls_url}")
            press_enter()
        elif choice == "p" and info.get("nav_prev"):
            href = info["nav_prev"]
            nums = re.findall(r"(\d+)x(\d+)", href)
            if nums:
                s, e = int(nums[0][0]), int(nums[0][1])
                new_info = cmd_series_episode(info["slug"], s, e)
                new_hls = cmd_series_stream(info["slug"], s, e)
                show_servers_dialog(new_info, new_hls)
                return
        elif choice == "n" and info.get("nav_next"):
            href = info["nav_next"]
            nums = re.findall(r"(\d+)x(\d+)", href)
            if nums:
                s, e = int(nums[0][0]), int(nums[0][1])
                new_info = cmd_series_episode(info["slug"], s, e)
                new_hls = cmd_series_stream(info["slug"], s, e)
                show_servers_dialog(new_info, new_hls)
                return
        elif choice.startswith("d"):
            num = choice[1:]
            if num.isdigit() and downloads:
                idx = int(num) - 1
                if 0 <= idx < len(downloads):
                    url = downloads[idx]["download_url"] or downloads[idx]["url"]
                    import webbrowser
                    webbrowser.open(url)
                    print(f"  {C['green']}Abriendo navegador...{C['reset']}")
                    press_enter()
                    return
            print(f"  {C['red']}Inválido.{C['reset']}")
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(streams):
                import webbrowser
                webbrowser.open(streams[idx]["url"])
                print(f"  {C['green']}Abriendo navegador...{C['reset']}")
                press_enter()
                return
            print(f"  {C['red']}Inválido.{C['reset']}")
        else:
            print(f"  {C['red']}Inválido.{C['reset']}")


def pick_movie_flow(movies):
    """Flow to pick a movie from list and show details"""
    show_movies(movies)
    if not movies:
        press_enter()
        return
    while True:
        idx = menu_nav()
        if idx is None:
            return
        if 0 <= idx < len(movies):
            movie = movies[idx]
            info = cmd_movie_info(movie["slug"])
            hls = cmd_movie_stream(movie["slug"])
            show_servers_dialog(info, hls)
            return
        print(f"  {C['red']}Número inválido.{C['reset']}")


def pick_series_episode_flow(slug):
    """Flow: pick season → pick episode → show links"""
    info = cmd_series_episode(slug, 1, 1)
    seasons = info["seasons"]
    if not seasons:
        print(f"  {C['yellow']}No se encontraron temporadas.{C['reset']}")
        press_enter()
        return

    # Season picker
    clear()
    print(f"\n  {C['bold']}{info['title']} - Seleccionar temporada{C['reset']}")
    print(f"  {C['gray']}{'─'*40}{C['reset']}")
    for i, s in enumerate(seasons):
        print(f"  {C['cyan']}[{i+1}]{C['reset']} Temporada {s}")
    print(f"  {C['red']}[B]{C['reset']} Volver")

    while True:
        choice = input(f"\n  {C['bold']}➜{C['reset']} ").strip().lower()
        if choice == "b":
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(seasons):
                snum = seasons[idx]
                # Get episodes for this season
                episodes = cmd_series_season_episodes(slug, snum)
                if not episodes:
                    print(f"  {C['yellow']}No se encontraron episodios.{C['reset']}")
                    press_enter()
                    continue

                # Episode picker
                clear()
                print(f"\n  {C['bold']}{info['title']} - Temporada {snum}{C['reset']}")
                print(f"  {C['gray']}{'─'*65}{C['reset']}")
                for i, ep in enumerate(episodes):
                    print(f"  {C['cyan']}[{i+1}]{C['reset']} {ep['season']}x{ep['episode']:02d} {ep['title'][:50]}")
                print(f"  {C['red']}[B]{C['reset']} Volver")

                while True:
                    ep_choice = input(f"\n  {C['bold']}➜{C['reset']} ").strip().lower()
                    if ep_choice == "b":
                        break
                    if ep_choice.isdigit():
                        ep_idx = int(ep_choice) - 1
                        if 0 <= ep_idx < len(episodes):
                            ep = episodes[ep_idx]
                            ep_info = cmd_series_episode(slug, ep["season"], ep["episode"])
                            hls = cmd_series_stream(slug, ep["season"], ep["episode"])
                            show_servers_dialog(ep_info, hls)
                            return
                    print(f"  {C['red']}Inválido.{C['reset']}")
                break
        print(f"  {C['red']}Inválido.{C['reset']}")


def movie_menu():
    while True:
        banner()
        print(f"  {C['bold']}🎬  Películas{C['reset']}")
        print(f"  {C['gray']}{'─'*40}{C['reset']}")
        print(f"  {C['cyan']}[1]{C['reset']} 🔍  Buscar")
        print(f"  {C['cyan']}[2]{C['reset']} 📋  Estrenos")
        print(f"  {C['cyan']}[3]{C['reset']} 🔥  Populares")
        print(f"  {C['cyan']}[4]{C['reset']} ✨  Últimas agregadas")
        print(f"  {C['red']}[B]{C['reset']}  Volver al menú principal")
        print()

        choice = input(f"  {C['bold']}➜{C['reset']} ").strip()

        if choice.lower() == "b":
            return
        if choice == "1":
            query = input(f"\n  {C['bold']}Nombre: {C['reset']}").strip()
            if not query:
                continue
            try:
                movies = cmd_search(query)
            except Exception as e:
                print(f"  {C['red']}Error: {e}{C['reset']}")
                press_enter()
                continue
            pick_movie_flow(movies)
        elif choice in ("2", "3", "4"):
            cat = {"2": "estrenos", "3": "populares", "4": "ultimas-agregadas"}[choice]
            try:
                movies = cmd_list(cat)
            except Exception as e:
                print(f"  {C['red']}Error: {e}{C['reset']}")
                press_enter()
                continue
            pick_movie_flow(movies)
        else:
            print(f"  {C['red']}Inválido.{C['reset']}")
            press_enter()


def series_menu():
    while True:
        banner()
        print(f"  {C['bold']}📺  Series{C['reset']}")
        print(f"  {C['gray']}{'─'*40}{C['reset']}")
        print(f"  {C['cyan']}[1]{C['reset']} 🔍  Buscar serie")
        print(f"  {C['cyan']}[2]{C['reset']} 🔥  Populares")
        print(f"  {C['cyan']}[3]{C['reset']} 📋  Estrenos")
        print(f"  {C['cyan']}[4]{C['reset']} ✨  Últimas agregadas")
        print(f"  {C['cyan']}[5]{C['reset']} 🆕  Últimos episodios")
        print(f"  {C['red']}[B]{C['reset']}  Volver al menú principal")
        print()

        choice = input(f"  {C['bold']}➜{C['reset']} ").strip()

        if choice.lower() == "b":
            return
        if choice == "1":
            query = input(f"\n  {C['bold']}Nombre de la serie: {C['reset']}").strip()
            if not query:
                continue
            try:
                series = cmd_series_search(query)
            except Exception as e:
                print(f"  {C['red']}Error: {e}{C['reset']}")
                press_enter()
                continue
            clear()
            print(f"\n  {C['bold']}Resultados para: {query}{C['reset']}")
            show_movies(series)
            if not series:
                press_enter()
                continue
            while True:
                idx = menu_nav()
                if idx is None:
                    break
                if 0 <= idx < len(series):
                    pick_series_episode_flow(series[idx]["slug"])
                    break
                print(f"  {C['red']}Inválido.{C['reset']}")
        elif choice in ("2", "3", "4", "5"):
            cat = {"2": "populares", "3": "estrenos", "4": "ultimas-agregadas", "5": "ultimos-episodios"}[choice]
            try:
                series = cmd_series_list(cat)
            except Exception as e:
                print(f"  {C['red']}Error: {e}{C['reset']}")
                press_enter()
                continue
            show_movies(series)
            if not series:
                press_enter()
                continue
            while True:
                idx = menu_nav()
                if idx is None:
                    break
                if 0 <= idx < len(series):
                    pick_series_episode_flow(series[idx]["slug"])
                    break
                print(f"  {C['red']}Inválido.{C['reset']}")
        else:
            print(f"  {C['red']}Inválido.{C['reset']}")
            press_enter()


def main_menu():
    while True:
        banner()
        print(f"  {C['bold']}Menú Principal{C['reset']}")
        print(f"  {C['gray']}{'─'*40}{C['reset']}")
        print(f"  {C['cyan']}[1]{C['reset']} 🎬  Películas")
        print(f"  {C['cyan']}[2]{C['reset']} 📺  Series")
        print(f"  {C['red']}[3]{C['reset']} 🚪  Salir")
        print()

        choice = input(f"  {C['bold']}➜{C['reset']} ").strip()

        if choice == "3" or choice.lower() == "q":
            print(f"\n  {C['green']}¡Hasta luego!{C['reset']}")
            sys.exit(0)
        elif choice == "1":
            movie_menu()
        elif choice == "2":
            series_menu()
        else:
            print(f"  {C['red']}Inválido.{C['reset']}")
            press_enter()


# ── CLI mode ─────────────────────────────────────────────────────

def cli_mode():
    p = argparse.ArgumentParser(prog="juanita", description="CLI para pelisjuanita.com")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Películas
    sp = sub.add_parser("search", help="Buscar películas")
    sp.add_argument("query")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("list", help="Listar películas")
    sp.add_argument("--category", default="estrenos", choices=["estrenos", "populares", "ultimas-agregadas"])
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("info", help="Info + servidores de una película")
    sp.add_argument("slug")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("stream", help="URL directa HLS de la película")
    sp.add_argument("slug")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("download", help="Enlace de descarga")
    sp.add_argument("slug")
    sp.add_argument("--lang", default=None, choices=["latino", "español", "subtitulada"])
    sp.add_argument("--index", type=int, default=0)
    sp.add_argument("--json", action="store_true")

    # Series
    sp = sub.add_parser("series-search", help="Buscar series")
    sp.add_argument("query")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("series-list", help="Listar series")
    sp.add_argument("--category", default="populares", choices=["populares", "estrenos", "ultimas-agregadas", "ultimos-episodios"])
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("series-episode", help="Info + servidores de un episodio")
    sp.add_argument("slug")
    sp.add_argument("season", type=int)
    sp.add_argument("episode", type=int)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("series-stream", help="URL directa HLS de un episodio")
    sp.add_argument("slug")
    sp.add_argument("season", type=int)
    sp.add_argument("episode", type=int)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("series-seasons", help="Listar temporadas de una serie")
    sp.add_argument("slug")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("series-episodes", help="Listar episodios de una temporada")
    sp.add_argument("slug")
    sp.add_argument("season", type=int)
    sp.add_argument("--json", action="store_true")

    args = p.parse_args()

    # Normalizar slug
    if hasattr(args, "slug") and args.slug and args.slug.startswith("http"):
        args.slug = args.slug.rstrip("/").split("/")[-1]

    try:
        if args.cmd == "search":
            movies = cmd_search(args.query, args.page)
            output_list(movies, args.json)
        elif args.cmd == "list":
            movies = cmd_list(args.category, args.page)
            output_list(movies, args.json)
        elif args.cmd == "info":
            info = cmd_movie_info(args.slug)
            output_info(info, args.json)
        elif args.cmd == "stream":
            url = cmd_movie_stream(args.slug)
            if args.json:
                print(json.dumps({"url": url}, indent=2))
            else:
                if url:
                    print(f"\n  URL del video (HLS):\n  {url}")
                else:
                    eprint("No se encontró stream para esta película.")
                    sys.exit(1)
        elif args.cmd == "download":
            dl = cmd_movie_download(args.slug, args.lang, args.index)
            if args.json:
                print(json.dumps(dl, indent=2, ensure_ascii=False))
            else:
                if dl:
                    url = dl["download_url"] or dl["url"]
                    print(f"\n  [{dl['lang']}] {dl['name']} - {dl['quality']}")
                    print(f"  URL: {url}")
                else:
                    eprint("No se encontró enlace de descarga.")
                    sys.exit(1)

        # Series
        elif args.cmd == "series-search":
            series = cmd_series_search(args.query, args.page)
            output_list(series, args.json)
        elif args.cmd == "series-list":
            series = cmd_series_list(args.category, args.page)
            output_list(series, args.json)
        elif args.cmd == "series-episode":
            info = cmd_series_episode(args.slug, args.season, args.episode)
            if args.json:
                print(json.dumps(info, indent=2, ensure_ascii=False))
            else:
                output_info(info, args.json)
        elif args.cmd == "series-stream":
            url = cmd_series_stream(args.slug, args.season, args.episode)
            if args.json:
                print(json.dumps({"url": url}, indent=2))
            else:
                if url:
                    print(f"\n  URL del video (HLS):\n  {url}")
                else:
                    eprint("No se encontró stream directo para este episodio.")
                    sys.exit(1)

        elif args.cmd == "series-seasons":
            info = cmd_series_episode(args.slug, 1, 1)
            seasons = info["seasons"]
            if args.json:
                print(json.dumps({"title": info["title"], "seasons": seasons}, indent=2, ensure_ascii=False))
            else:
                print(f"\n  {info['title']}")
                for s in seasons:
                    print(f"    Temporada {s}")
        elif args.cmd == "series-episodes":
            eps = cmd_series_season_episodes(args.slug, args.season)
            if args.json:
                print(json.dumps(eps, indent=2, ensure_ascii=False))
            else:
                print(f"\n  {args.slug} - Temporada {args.season}")
                for ep in eps:
                    print(f"    {ep['season']}x{ep['episode']:02d} {ep['title']}")

    except requests.RequestException as e:
        eprint(f"Error de conexión: {e}")
        sys.exit(1)
    except Exception as e:
        eprint(f"Error: {e}")
        sys.exit(1)


def output_list(movies, json_mode):
    if json_mode:
        print(json.dumps(movies, indent=2, ensure_ascii=False))
    else:
        if not movies:
            print("Sin resultados.")
            return
        print(f"\n  {'★':<4} {'Año':<6} {'Título':<50} Slug")
        print(f"  {'─'*4} {'─'*6} {'─'*50} {'─'*30}")
        for m in movies:
            print(f"  {m['rating']:<4} {m['year']:<6} {m['title'][:48]:<50} {m['slug']}")


def output_info(info, json_mode):
    if json_mode:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print(f"\n  {info['title']}")
        if info.get("episode_label"):
            print(f"  {info['episode_label']}")
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
