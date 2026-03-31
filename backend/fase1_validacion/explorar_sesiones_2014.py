import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://opendata.congreso.cl/wscamaradiputados.asmx"

# Obtener todas las legislaturas
r = requests.get(f"{BASE}/getLegislaturas", headers=HEADERS, timeout=15)
parser = etree.XMLParser(recover=True)
root = etree.fromstring(r.content, parser=parser)

ns = "http://tempuri.org/"

# Filtrar legislaturas desde 2014
print("Legislaturas desde 2014:")
legs_2014 = []
for leg in root.iter(f"{{{ns}}}Legislatura"):
    fecha_inicio = leg.find(f"{{{ns}}}FechaInicio")
    leg_id       = leg.find(f"{{{ns}}}ID")
    numero       = leg.find(f"{{{ns}}}Numero")
    tipo         = leg.find(f"{{{ns}}}Tipo")

    if fecha_inicio is None or leg_id is None:
        continue

    fecha_str = fecha_inicio.text[:10] if fecha_inicio.text else ""
    if fecha_str >= "2014-01-01":
        legs_2014.append({
            "id":     leg_id.text,
            "numero": numero.text if numero is not None else "?",
            "tipo":   tipo.text if tipo is not None else "?",
            "inicio": fecha_str,
        })
        print(f"  ID={leg_id.text} | N°{numero.text if numero is not None else '?'} | {tipo.text if tipo is not None else '?'} | {fecha_str}")

print(f"\nTotal legislaturas desde 2014: {len(legs_2014)}")

# Contar sesiones por legislatura
print("\nSesiones por legislatura:")
total_sesiones = 0
for leg in legs_2014:
    r2 = requests.get(
        f"{BASE}/getSesiones?prmLegislaturaID={leg['id']}",
        headers=HEADERS, timeout=15
    )
    root2 = etree.fromstring(r2.content, parser=parser)
    sesiones = list(root2.iter(f"{{{ns}}}Sesion"))
    # Solo celebradas
    celebradas = [s for s in sesiones
                  if s.find(f"{{{ns}}}Estado") is not None
                  and s.find(f"{{{ns}}}Estado").get("Codigo") == "1"]
    total_sesiones += len(celebradas)
    print(f"  Leg {leg['id']} ({leg['inicio']}): {len(sesiones)} sesiones ({len(celebradas)} celebradas)")

print(f"\nTotal sesiones celebradas desde 2014: {total_sesiones}")
print(f"Tiempo estimado de carga: ~{total_sesiones * 1.5 / 60:.1f} minutos")
