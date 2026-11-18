"""Pone en fuente.json las capturas, la cabecera y las imágenes de las noticias.

Lo ejecuta el workflow "Actualizar fuente" cuando cambias algo en las
carpetas `capturas/` o `imagenes/` (y también al publicar una Release).

- capturas/: todas las imágenes .png/.jpg, en orden por nombre
  (1-inicio.png, 2-calcular.png…). Se quitan solas si las borras.
- imagenes/cabecera.png: imagen ancha de la fuente (1500×500).
- imagenes/noticia.png: imagen de la noticia de bienvenida.
- imagenes/<identificador>.png: imagen de la noticia con ese identificador.
"""
import json
import os
import re
import struct
from urllib.parse import quote

REPO = os.environ.get("GITHUB_REPOSITORY", "Atypicapp/I3D")
BASE = f"https://raw.githubusercontent.com/{REPO}/main/"
EXT = (".png", ".jpg", ".jpeg")


def tamano(ruta):
    """Ancho y alto de un PNG o JPEG sin librerías externas."""
    with open(ruta, "rb") as f:
        cab = f.read(26)
        if cab[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", cab[16:24])
        f.seek(2)
        while True:
            marca = f.read(2)
            if len(marca) < 2 or marca[0] != 0xFF:
                return None
            if marca[1] in (0xC0, 0xC1, 0xC2):
                f.read(3)
                alto, ancho = struct.unpack(">HH", f.read(4))
                return ancho, alto
            largo = struct.unpack(">H", f.read(2))[0]
            f.seek(largo - 2, 1)


def orden(nombre):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", nombre)]


with open("fuente.json", encoding="utf-8") as f:
    fuente = json.load(f)
app = fuente["apps"][0]

# Capturas
capturas = []
if os.path.isdir("capturas"):
    for nombre in sorted(os.listdir("capturas"), key=orden):
        if not nombre.lower().endswith(EXT):
            continue
        dim = tamano(os.path.join("capturas", nombre))
        if not dim:
            continue
        ancho, alto = dim
        # Capturas de iPhone a 3x: se guardan en puntos (como en TimiCal).
        escala = 3 if ancho >= 1000 else (2 if ancho >= 700 else 1)
        capturas.append({
            "imageURL": BASE + "capturas/" + quote(nombre),
            "width": round(ancho / escala),
            "height": round(alto / escala),
        })
app["screenshots"] = capturas
app["screenshotURLs"] = [c["imageURL"] for c in capturas]

# Cabecera de la fuente
if os.path.isfile("imagenes/cabecera.png"):
    fuente["headerURL"] = BASE + "imagenes/cabecera.png"
else:
    fuente.pop("headerURL", None)

# Imágenes de las noticias
for noticia in fuente.get("news", []):
    ident = noticia.get("identifier", "")
    candidatos = [f"imagenes/{ident}.png", f"imagenes/{ident}.jpg"]
    if ident.startswith("bienvenida"):
        candidatos.append("imagenes/noticia.png")
    ruta = next((c for c in candidatos if os.path.isfile(c)), None)
    if ruta:
        noticia["imageURL"] = BASE + quote(ruta)

fuente["featuredApps"] = [app["bundleIdentifier"]]

with open("fuente.json", "w", encoding="utf-8") as f:
    json.dump(fuente, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Capturas: {len(capturas)}")
