import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://opendata.congreso.cl/wscamaradiputados.asmx"
NS   = "http://tempuri.org/"

# Obtener sesiones de legislatura 57 (2025 — ya cerrada, debería tener datos)
print("Sesiones legislatura 57 (2025):")
r = requests.get(f"{BASE}/getSesiones?prmLegislaturaID=57", headers=HEADERS, timeout=15)
parser = etree.XMLParser(recover=True)
root = etree.fromstring(r.content, parser=parser)

sesiones = []
for s in root.findall(f".//{{{NS}}}Sesion"):
    sid    = s.find(f"{{{NS}}}ID")
    fecha  = s.find(f"{{{NS}}}Fecha")
    estado = s.find(f"{{{NS}}}Estado")
    if estado is not None and estado.get("Codigo") == "1":  # solo celebradas
        sesiones.append({
            "id":    sid.text if sid is not None else "?",
            "fecha": fecha.text[:10] if fecha is not None and fecha.text else "?",
        })

print(f"Total celebradas: {len(sesiones)}")
print(f"Primeras 5: {sesiones[:5]}")
print(f"Últimas 5:  {sesiones[-5:]}")

# Probar detalle de las últimas 3 sesiones
print("\nDetalle de últimas 3 sesiones:")
for s in sesiones[-3:]:
    r2 = requests.get(f"{BASE}/getSesionDetalle?prmSesionId={s['id']}", headers=HEADERS, timeout=15)
    root2 = etree.fromstring(r2.content, parser=parser)
    asistentes = root2.findall(f".//{{{NS}}}AsistenteSala")
    
    # Tipos de asistencia
    tipos = {}
    for a in asistentes:
        asist = a.find(f"{{{NS}}}Asistencia")
        if asist is not None:
            texto = asist.text.strip() if asist.text else "?"
            tipos[texto] = tipos.get(texto, 0) + 1
    
    print(f"\n  Sesión {s['id']} ({s['fecha']}): {len(r2.content)} bytes | {len(asistentes)} asistentes")
    for tipo, count in tipos.items():
        print(f"    {tipo}: {count}")
    
    # Mostrar primeros 2 registros
    if asistentes:
        for a in asistentes[:2]:
            asist  = a.find(f"{{{NS}}}Asistencia")
            dipid  = a.find(f".//{{{NS}}}DIPID")
            nombre = a.find(f".//{{{NS}}}Nombre")
            apell  = a.find(f".//{{{NS}}}Apellido_Paterno")
            just   = a.find(f"{{{NS}}}Justificacion")
            print(f"    → {nombre.text if nombre is not None else '?'} "
                  f"{apell.text if apell is not None else '?'} | "
                  f"{asist.text.strip() if asist is not None and asist.text else '?'} | "
                  f"just={just.text if just is not None else 'Sin justificación'}")
