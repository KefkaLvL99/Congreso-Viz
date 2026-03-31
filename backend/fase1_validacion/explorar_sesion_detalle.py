import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://opendata.congreso.cl/wscamaradiputados.asmx"
NS   = "http://tempuri.org/"

# Sesión 4761 — celebrada el 25/03/2026
r = requests.get(f"{BASE}/getSesionDetalle?prmSesionId=4761", headers=HEADERS, timeout=15)
parser = etree.XMLParser(recover=True)
root = etree.fromstring(r.content, parser=parser)

print(f"HTTP: 200 | {len(r.content)} bytes\n")

# Mostrar estructura completa
def imprimir(nodo, nivel=0, max_nivel=5, max_hijos=3):
    indent = "  " * nivel
    attrs  = " ".join(f'{k}="{v}"' for k, v in nodo.attrib.items())
    tag    = nodo.tag.replace(f"{{{NS}}}", "")
    texto  = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
    linea  = f"{indent}<{tag}"
    if attrs: linea += f" {attrs}"
    linea += ">"
    if texto: linea += f" → '{texto[:60]}'"
    print(linea)
    hijos = list(nodo)
    for i, hijo in enumerate(hijos):
        if i >= max_hijos and nivel > 1:
            print(f"{indent}  ... ({len(hijos) - max_hijos} más)")
            break
        if nivel < max_nivel:
            imprimir(hijo, nivel+1, max_nivel, max_hijos)

imprimir(root, max_nivel=5, max_hijos=3)

# Estadísticas
asistentes = root.findall(f".//{{{NS}}}AsistenteSala")
print(f"\nTotal asistentes: {len(asistentes)}")

# Tipos de asistencia disponibles
tipos = set()
for a in asistentes:
    asist = a.find(f"{{{NS}}}Asistencia")
    if asist is not None:
        tipos.add(f"Codigo={asist.get('Codigo')} Asiste={asist.get('Asiste')} texto='{asist.text.strip() if asist.text else ''}'")

print(f"\nTipos de asistencia:")
for t in sorted(tipos):
    print(f"  {t}")
