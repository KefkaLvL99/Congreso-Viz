import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Probar distintos parámetros y fechas
urls = [
    # Fecha específica antigua
    "https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha=01/06/2015",
    "https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha=15/06/2015",
    # Con parámetro de año
    "https://tramitacion.senado.cl/wspublico/tramitacion.php?anio=2015",
    # Con fecha de inicio y fin
    "https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha_inicio=01/01/2015&fecha_fin=31/12/2015",
    # Por sesión
    "https://tramitacion.senado.cl/wspublico/tramitacion.php?sesion=1&anio=2015",
]

for url in urls:
    r = requests.get(url, headers=HEADERS, timeout=20)
    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(r.content, parser=parser)
        proyectos = list(root.iter("proyecto"))
        votaciones = list(root.iter("votacion"))
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        print(f"  Proyectos: {len(proyectos)} | Votaciones: {len(votaciones)}")
        if votaciones:
            v = votaciones[0]
            fecha = v.find("FECHA")
            print(f"  Primera votación fecha: {fecha.text if fecha is not None else '?'}")
    except Exception as e:
        print(f"\n{url}")
        print(f"  Error: {e}")
        print(f"  Respuesta: {r.text[:200]}")
