import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "http://opendata.camara.cl/camaradiputados/pages"

urls = [
    # Votaciones por año — clave para histórico
    f"{BASE}/legislativo/retornarVotacionesXAnno.aspx?prmAnno=2026",
    f"{BASE}/legislativo/retornarVotacionesXAnno.aspx?prmAnno=2025",
    # Detalle de votación
    f"{BASE}/legislativo/retornarVotacionDetalle.aspx?prmVotacionId=88519",
    # Sesiones por año
    f"{BASE}/sala/retornarSesionesXAnno.aspx?prmAnno=2026",
    # Asistencia por sesión
    f"{BASE}/sala/retornarSesionAsistencia.aspx?prmSesionId=4761",
    # Proyectos de ley
    f"{BASE}/legislativo/retornarProyectoLey.aspx?prmNumeroBoletin=18137-05",
]

parser = etree.XMLParser(recover=True)

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=100)
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        if r.status_code == 200 and len(r.content) > 100:
            try:
                root = etree.fromstring(r.content, parser=parser)
                hijos = list(root)
                print(f"  Tag raíz: {root.tag} | Hijos: {len(hijos)}")
                if hijos:
                    print(f"  Primer hijo: {hijos[0].tag}")
                    # Mostrar primeros 3 registros
                    for hijo in hijos[:3]:
                        campos = {c.tag: c.text for c in hijo if c.text}
                        print(f"  → {campos}")
            except:
                print(f"  Contenido: {r.text[:300]}")
    except Exception as e:
        print(f"\n{url} → Error: {e}")
