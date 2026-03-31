import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://opendata.congreso.cl/wscamaradiputados.asmx"
NS   = "http://tempuri.org/"

parser = etree.XMLParser(recover=True)

# Probar sesiones antiguas de distintas legislaturas
ids_probar = [
    ("2005", 1),
    ("2010", 1000),
    ("2014", 2000),
    ("2016", 2500),
    ("2018", 3000),
    ("2020", 3500),
    ("2022", 4000),
    ("2023", 4200),
    ("2024", 4400),
    ("2025-inicio", 4628),
    ("2025-medio", 4680),
    ("2025-fin", 4740),
    ("2026", 4761),
]

for label, sid in ids_probar:
    r = requests.get(f"{BASE}/getSesionDetalle?prmSesionId={sid}", headers=HEADERS, timeout=15)
    root = etree.fromstring(r.content, parser=parser)
    asistentes = root.findall(f".//{{{NS}}}AsistenteSala")
    fecha = root.find(f".//{{{NS}}}Fecha")
    print(f"  ~{label} | ID={sid} | {len(r.content):6d} bytes | {len(asistentes):3d} asistentes | "
          f"fecha={fecha.text[:10] if fecha is not None and fecha.text else '?'}")
