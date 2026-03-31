# ============================================================
# scraper_senadores_web.py
# ============================================================
# Obtiene los 50 senadores vigentes desde senado.cl
# ============================================================

import re
import requests
from bs4 import BeautifulSoup

URL = "https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"}

# Prefijos de apellidos compuestos — no se separan
PREFIJOS_APELLIDO = {"de", "del", "de la", "van", "von", "kaiser"}


def _separar_nombre(nombre_completo: str) -> dict:
    """
    Separa nombre completo en partes considerando apellidos compuestos.
    'Alfonso De Urresti Longton' → nombre=Alfonso, ap=De Urresti, am=Longton
    'Enrique Van Rysselberghe Herrera' → nombre=Enrique, ap=Van Rysselberghe, am=Herrera
    'Vanessa Kaiser Barents-Von Hohenhagen' → nombre=Vanessa Kaiser, ap=Barents-Von, am=Hohenhagen
    'Miguel Ángel Becker Alvear' → nombre=Miguel Ángel, ap=Becker, am=Alvear
    'Camila Flores Oporto' → nombre=Camila, ap=Flores, am=Oporto
    """
    partes = nombre_completo.split()

    if len(partes) < 2:
        return {"nombre": nombre_completo, "apellido_paterno": nombre_completo, "apellido_materno": ""}

    # Detectar si hay prefijo de apellido en la posición penúltima o antepenúltima
    # Ej: "De Urresti" → partes[-3]="De", partes[-2]="Urresti", partes[-1]="Longton"
    # Ej: "Van Rysselberghe" → partes[-3]="Van", partes[-2]="Rysselberghe", partes[-1]="Herrera"

    if len(partes) >= 4:
        posible_prefijo = partes[-3].lower()
        if posible_prefijo in PREFIJOS_APELLIDO:
            # apellido paterno = prefijo + siguiente palabra
            apellido_paterno = f"{partes[-3]} {partes[-2]}"
            apellido_materno = partes[-1]
            nombre = " ".join(partes[:-3])
            return {"nombre": nombre, "apellido_paterno": apellido_paterno, "apellido_materno": apellido_materno}

    if len(partes) >= 3:
        # Caso normal: últimas 2 son apellidos, resto es nombre
        apellido_materno = partes[-1]
        apellido_paterno = partes[-2]
        nombre = " ".join(partes[:-2])
        return {"nombre": nombre, "apellido_paterno": apellido_paterno, "apellido_materno": apellido_materno}

    # Solo 2 palabras
    return {"nombre": partes[0], "apellido_paterno": partes[-1], "apellido_materno": ""}


def obtener_senadores_web(verbose: bool = True) -> list[dict]:
    """
    Scraping del sitio oficial del Senado.
    Retorna lista de 50 senadores con todos sus datos.
    """
    if verbose:
        print("  → Scraping senadores desde senado.cl...")

    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, "html.parser")
    senadores = []

    for card in soup.find_all("a", href=True):
        h3 = card.find("h3")
        if not h3:
            continue

        nombre_completo = h3.get_text(strip=True)
        # Limpiar espacios dobles
        nombre_completo = re.sub(r"\s+", " ", nombre_completo).strip()

        if not nombre_completo or len(nombre_completo) < 5:
            continue

        items = card.find_all("li")
        circunscripcion = None
        region          = None
        partido         = None

        for li in items:
            h4 = li.find("h4")
            if not h4:
                continue
            label          = h4.get_text(strip=True)
            texto_completo = li.get_text(strip=True)
            valor          = texto_completo.replace(label, "").strip()

            if "Circunscripción" in label:
                circunscripcion = label.replace("Circunscripción", "").strip()
                region          = valor
            elif "Partido" in label:
                partido = label.replace("Partido", "").strip()

        if not nombre_completo or not partido:
            continue

        partes_nombre = _separar_nombre(nombre_completo)

        senador_id = f"WEB-{re.sub(r'[^a-zA-Z]', '', nombre_completo.lower())[:20]}"

        senadores.append({
            "id":               senador_id,
            "nombre_completo":  nombre_completo,
            "nombre":           partes_nombre["nombre"],
            "apellido_paterno": partes_nombre["apellido_paterno"],
            "apellido_materno": partes_nombre["apellido_materno"],
            "partido":          partido,
            "region":           region,
            "circunscripcion":  circunscripcion,
            "telefono":         None,
            "email":            None,
            "curriculum_url":   None,
        })

    if verbose:
        print(f"  ✅ Senadores desde web: {len(senadores)}")

    return senadores


if __name__ == "__main__":
    senadores = obtener_senadores_web()
    print(f"\nTotal: {len(senadores)}\n")

    # Verificar casos especiales
    especiales = ["De Urresti", "Van Rysselberghe", "Kaiser", "Flores", "Cruz-Coke"]
    print("Verificando casos especiales:")
    for s in senadores:
        for e in especiales:
            if e.lower() in s["nombre_completo"].lower():
                print(f"  {s['nombre_completo']}")
                print(f"    nombre='{s['nombre']}' | ap='{s['apellido_paterno']}' | am='{s['apellido_materno']}'")
                print(f"    partido={s['partido']}")
