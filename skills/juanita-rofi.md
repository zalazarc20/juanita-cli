# Juanita Rofi — Integración con Rofi Launcher

Busca películas y series desde Rofi con selección de servidores y posters.

## Requisitos

- [Rofi](https://github.com/davatorium/rofi) 1.7+
- `jq` — para parsear JSON
- `curl` — para descargar posters
- `mpv` o `vlc` — para reproducir streams HLS
- `xdg-utils` — para abrir URLs en el navegador
- Juanita CLI instalado globalmente (ver `juanita-install.md`)
- (Opcional) Kitty terminal — para mostrar posters con `kitty +kitten icat`

## Instalación

```bash
# Desde el repo
sudo ln -s "$PWD/juanita-rofi" /usr/local/bin/juanita-rofi

# O copiarlo
sudo cp juanita-rofi /usr/local/bin/
chmod +x /usr/local/bin/juanita-rofi
```

Si no tenés permisos sudo, copiá a `~/.local/bin/` y asegurate que esté en el PATH:

```bash
mkdir -p ~/.local/bin
cp juanita-rofi ~/.local/bin/
chmod +x ~/.local/bin/juanita-rofi
export PATH="$HOME/.local/bin:$PATH"
```

## Integración con Rofi (drun / launcher de apps)

Para que aparezca al buscar con Super+r (modo Apps/drun):

```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/juanita-rofi.desktop << 'EOF'
[Desktop Entry]
Name=Juanita
Comment=Buscar películas y series en pelisjuanita.com
Exec=/home/usuario/.local/bin/juanita-rofi
Terminal=false
Type=Application
Categories=Utility;
EOF
```

Ajustar `Exec` con la ruta absoluta al script. Después de crearlo, aparece en Rofi al escribir "Juanita" con Super+r.

## Uso

```bash
# Desde terminal
juanita-rofi

# O desde rofi directamente
rofi -show drun -display-drun "Apps"  # buscar "Juanita"
```

## Flujo de uso

1. Rofi pide el término de búsqueda (ej: "avatar")
2. Muestra resultados combinados de películas 🎬 y series 📺
3. Al seleccionar uno, ofrece acciones:

### Películas
- **▶ Ver/Stream** — muestra todos los servidores stream (Pelisjuanita, Streamwish, Earnvids, etc.) con idioma y calidad. Links `player.php` extraen HLS y abren VLC; los demás abren navegador.
- **⬇ Descargar** — muestra servidores de descarga (1fichier, Dood, etc.)
- **🖼 Ver poster** — abre el poster TMDB en el visor de imágenes
- **ℹ Info** — sinopsis y lista completa de servidores
- **🌐 Abrir en navegador** — abre en pelisjuanita.com

### Series
- **▶ Ver episodio** — navegación por temporada → episodio → selección de servidor stream
- **🖼 Ver poster**
- **🌐 Abrir en navegador**

## Comportamiento de streams

| Tipo de URL | Comportamiento |
|---|---|
| `player.php?id=...` | Extrae HLS directo → abre en VLC/mpv |
| Streamwish, Earnvids, Nupload, etc. | Abre en el navegador |
| Descarga (1fichier, Dood, etc.) | Abre en el navegador |

## Atajo de teclado

Para i3/Hyprland/Sway:

```
bindsym $mod+Shift+j exec kitty -e juanita-rofi
```
