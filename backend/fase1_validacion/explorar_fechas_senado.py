import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# El endpoint devuelve proyectos modificados DESDE esa fecha
# Probemos con fechas recientes que sabemos que tienen datos
fechas = [
    "25/03/2026",  # hoy — sabemos que tiene datos
    "18/03/2026",  # hace una semana — tiene datos
    "01/03/2026",  # inicio de marzo
    "01/01/2026",  # inicio de año
    "01/10/2025",  # hace 6 meses
    "01/01/2025",  # hace 1 año
    "01/01/2024",  # hace 2 años
    "01/01/2023",  # hace 3 años
]

for fecha in fechas:
    url = f"https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(r.content, parser=parser)
        proyectos = list(root.iter("proyecto"))
        votaciones = list(root.iter("votacion"))
        
        # Obtener rango de fechas de las votaciones
        fechas_vot = []
        for v in root.iter("votacion"):
            f = v.find("FECHA")
            if f is not None and f.text:
                fechas_vot.append(f.text.strip())
        
        fecha_min = min(fechas_vot) if fechas_vot else "?"
        fecha_max = max(fechas_vot) if fechas_vot else "?"
        
        print(f"fecha={fecha}: {len(r.content)} bytes | {len(proyectos)} proyectos | {len(votaciones)} votaciones | rango: {fecha_min} → {fecha_max}")
    except Exception as e:
        print(f"fecha={fecha}: Error — {e}")
