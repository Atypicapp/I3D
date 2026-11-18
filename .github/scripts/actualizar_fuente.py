"""Añade la versión de una Release de GitHub a fuente.json.

Lo ejecuta el workflow "Actualizar fuente" cada vez que se publica una
Release. Lee del evento:
- la etiqueta (v1.1 -> versión 1.1),
- la descripción de la Release (novedades),
- el archivo .ipa adjunto (dirección y tamaño).
"""
import json
import os
import sys

with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
    evento = json.load(f)

release = evento["release"]
version = release["tag_name"].lstrip("vV").strip()
ipas = [a for a in release.get("assets", []) if a["name"].lower().endswith(".ipa")]
if not ipas:
    sys.exit("La Release no tiene ningún archivo .ipa adjunto.")
ipa = ipas[0]

import re


def limpiar(texto):
    """SideStore muestra el texto tal cual: se quitan los símbolos de Markdown."""
    lineas = []
    for l in texto.replace("\r\n", "\n").split("\n"):
        l = re.sub(r"^\s*#{1,6}\s*", "", l)          # títulos ###
        l = re.sub(r"\*\*(.+?)\*\*", r"\1", l)       # **negrita**
        l = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"\1", l)  # *cursiva*
        l = re.sub(r"`([^`]+)`", r"\1", l)            # `código`
        l = re.sub(r"^(\s*)[-*]\s+", r"\1• ", l)      # viñetas
        lineas.append(l.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


notas = limpiar(release.get("body") or "") or f"Versión {version}."
fecha = (release.get("published_at") or release.get("created_at") or "")[:10]

with open("fuente.json", encoding="utf-8") as f:
    fuente = json.load(f)

app = fuente["apps"][0]
versiones = [
    v for v in app.get("versions", [])
    if v.get("version") != version and "PENDIENTE" not in json.dumps(v)
]
nueva = {
    "version": version,
    "date": fecha,
    "localizedDescription": notas,
    "downloadURL": ipa["browser_download_url"],
    "size": ipa["size"],
    "minOSVersion": "17.0",
}
# SideStore y AltStore toman la PRIMERA de la lista como la más reciente.
app["versions"] = [nueva] + versiones

with open("fuente.json", "w", encoding="utf-8") as f:
    json.dump(fuente, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Fuente actualizada: {version} ({ipa['size']} bytes)")
