---
name: juanita-rofi
description: Use when the user asks about Rofi integration, launcher setup, .desktop files, or the juanita-rofi script for searching movies and series from Rofi.
---

# Juanita Rofi — Integración con Rofi

Script `juanita-rofi` para buscar películas/series desde Rofi con selección de servidores y posters TMDB.

## Instalación

```bash
sudo ln -s "$PWD/juanita-rofi" /usr/local/bin/juanita-rofi
# o sin sudo:
cp juanita-rofi ~/.local/bin/ && chmod +x ~/.local/bin/juanita-rofi
```

## Integrar en Rofi (drun/Apps)

```bash
cat > ~/.local/share/applications/juanita-rofi.desktop << 'EOF'
[Desktop Entry]
Name=Juanita
Comment=Buscar películas y series
Exec=/home/user/.local/bin/juanita-rofi
Terminal=false
Type=Application
Categories=Utility;
EOF
```

Usar la ruta absoluta en `Exec`. Luego aparece al escribir "Juanita" con Super+r.

## Flujo

1. Rofi pide búsqueda
2. Muestra 🎬 películas + 📺 series combinados
3. Al seleccionar:
   - **▶ Stream** → elige servidor → player.php extrae HLS (VLC) / otros van a navegador
   - **⬇ Descargar** → elige servidor → navegador
   - **🖼 Poster** → abre imagen
   - **ℹ Info** → sinopsis + servidores
   - **🌐 Abrir** → pelisjuanita.com
4. Series: navegación temporada → episodio → servidor

## Dependencias

- `rofi` 1.7+, `jq`, `curl`, `xdg-utils`
- `mpv` o `vlc` para HLS
- Kitty (opcional, para posters con icat)
