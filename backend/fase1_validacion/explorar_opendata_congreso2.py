import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

urls = [
    # Votaciones Cámara por boletín
    "https://opendata.congreso.cl/pages/votacion_boletin.aspx?prmBoletin=18137-05",
    "https://opendata.congreso.cl/pages/votacion_boletin.aspx?prmBoletin=16481-25",
    # Detalle votación
    "https://opendata.congreso.cl/pages/votacion_detalle.aspx?prmVotacionId=88519",
    # Sesiones
    "https://opendata.congreso.cl/pages/sesiones.aspx?prmAnno=2026",
    "https://opendata.congreso.cl/pages/sesion_detalle.aspx?prmSesionId=4761",
    # Asistencia
    "https://opendata.congreso.cl/pages/sesion_boletin.aspx?prmSesionId=4761",
]

parser = etree.XMLParser(recover=True)

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        if r.status_code == 200 and len(r.content) > 100:
            try:
                root = etree.fromstring(r.content, parser=parser)
                hijos = list(root)
                print(f"  Tag raíz: {root.tag} | Hijos: {len(hijos)}")
                for hijo in hijos[:2]:
                    campos = {c.tag: (c.text or '')[:50] for c in hijo if c.text}
                    print(f"  → {campos}")
            except:
                print(f"  Contenido: {r.text[:300]}")
    except Exception as e:
        print(f"\n{url} → Error: {e}")
