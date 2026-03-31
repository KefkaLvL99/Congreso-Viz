# ============================================================
# scraper_votaciones_camara_ws.py
# ============================================================

import time
import hashlib
import requests
from lxml import etree
from datetime import datetime, timezone

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE_WS  = "https://opendata.congreso.cl/wscamaradiputados.asmx"
URL_SEN  = "https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin={num}&tipo={tipo}"
NS       = "http://tempuri.org/"
TIMEOUT  = 20
PAUSA    = 0.3

# Cache de títulos para no consultar el mismo boletín múltiples veces
_cache_titulos: dict[str, str] = {}


def _texto(nodo, tag: str):
    e = nodo.find(f"{{{NS}}}{tag}")
    return e.text.strip() if e is not None and e.text else None


def hacer_id(boletin: str, vid: str) -> str:
    return f"CAM-{vid}"


def obtener_titulo_boletin(boletin: str) -> str | None:
    """Obtiene el título desde la API del Senado por boletín."""
    if boletin in _cache_titulos:
        return _cache_titulos[boletin]
    try:
        num, tipo = boletin.split("-", 1)
        url = URL_SEN.format(num=num, tipo=tipo)
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200 or len(r.content) < 200:
            return None
        parser = etree.XMLParser(recover=True)
        root   = etree.fromstring(r.content, parser=parser)
        t = root.find(".//titulo")
        titulo = t.text.strip() if t is not None and t.text else None
        if titulo:
            _cache_titulos[boletin] = titulo
        return titulo
    except Exception:
        return None


def obtener_votaciones_boletin(boletin: str) -> list[dict]:
    url = f"{BASE_WS}/getVotaciones_Boletin?prmBoletin={boletin}"
    parser = etree.XMLParser(recover=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200 or len(r.content) < 100:
            return []
        root = etree.fromstring(r.content, parser=parser)
        votaciones = []

        # Obtener título desde API del Senado (una sola vez por boletín)
        titulo = obtener_titulo_boletin(boletin)

        for v in root.findall(f"{{{NS}}}Votacion"):
            vid = _texto(v, "ID")
            if not vid:
                continue

            fecha_raw = _texto(v, "Fecha") or ""
            try:
                fecha = datetime.fromisoformat(fecha_raw).strftime("%d/%m/%Y")
            except Exception:
                fecha = fecha_raw[:10]

            res_nodo = v.find(f"{{{NS}}}Resultado")
            resultado_texto = res_nodo.text.strip() if res_nodo is not None and res_nodo.text else ""
            resultado = "Aprobado" if "Aprobado" in resultado_texto else \
                       ("Rechazado" if "Rechazado" in resultado_texto else "Empate")

            si   = int(_texto(v, "TotalAfirmativos")  or 0)
            no   = int(_texto(v, "TotalNegativos")    or 0)
            abs_ = int(_texto(v, "TotalAbstenciones") or 0)

            articulo = _texto(v, "Articulo") or ""
            tramite  = _texto(v, "Tramite")  or ""
            tema     = f"{tramite} — {articulo}".strip(" —") if articulo else tramite

            tipo_nodo = v.find(f"{{{NS}}}Tipo")
            tipo = tipo_nodo.text.strip() if tipo_nodo is not None and tipo_nodo.text else None

            votaciones.append({
                "vid":          vid,
                "boletin":      boletin,
                "titulo":       titulo,  # desde API Senado
                "fecha":        fecha,
                "tipo":         tipo,
                "resultado":    resultado,
                "votos_si":     si,
                "votos_no":     no,
                "abstenciones": abs_,
                "quorum":       _texto(v, "Quorum"),
                "tema":         tema[:500] if tema else None,
                "tramite":      tramite,
            })
        return votaciones
    except Exception:
        return []


def obtener_detalle_votacion(vid: str) -> list[dict]:
    url = f"{BASE_WS}/getVotacion_Detalle?prmVotacionId={vid}"
    parser = etree.XMLParser(recover=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        root = etree.fromstring(r.content, parser=parser)
        votos = []
        nodo_votos = root.find(f"{{{NS}}}Votos")
        if nodo_votos is None:
            return []
        for voto in nodo_votos.findall(f"{{{NS}}}Voto"):
            dip = voto.find(f"{{{NS}}}Diputado")
            nombre = None
            if dip is not None:
                nombre_nodo = dip.find(f"{{{NS}}}Nombre")
                apell_nodo  = dip.find(f"{{{NS}}}Apellido_Paterno")
                apell2_nodo = dip.find(f"{{{NS}}}Apellido_Materno")
                if nombre_nodo is not None and apell_nodo is not None:
                    ap  = apell_nodo.text.strip()  if apell_nodo.text  else ""
                    am  = apell2_nodo.text.strip()  if apell2_nodo is not None and apell2_nodo.text else ""
                    nom = nombre_nodo.text.strip()  if nombre_nodo.text else ""
                    nombre = f"{ap} {am}, {nom}".strip(" ,")

            opcion_nodo = voto.find(f"{{{NS}}}Opcion")
            opcion = opcion_nodo.text.strip() if opcion_nodo is not None and opcion_nodo.text else ""
            seleccion = "Si" if opcion == "Afirmativo" else \
                       ("No" if opcion == "Negativo" else \
                       ("Abstencion" if opcion in ("Abstención", "Abstencion") else opcion))

            if nombre:
                votos.append({"parlamentario": nombre, "seleccion": seleccion})
        return votos
    except Exception:
        return []


def sincronizar_camara_por_boletines(boletines: list[str], db, verbose=True) -> int:
    from models import Votacion, VotoDetalle
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    total_nuevas = 0

    for boletin in boletines:
        votaciones = obtener_votaciones_boletin(boletin)
        if not votaciones:
            time.sleep(PAUSA)
            continue

        nuevas_boletin = 0
        for vot in votaciones:
            vid        = vot["vid"]
            interno_id = hacer_id(boletin, vid)

            datos = {
                "id":            interno_id,
                "boletin":       boletin,
                "titulo":        vot.get("titulo"),
                "camara":        "C.Diputados",
                "etapa":         vot.get("tramite"),
                "estado":        None,
                "sesion":        None,
                "fecha":         vot["fecha"],
                "tema":          vot.get("tema"),
                "tipo_votacion": vot.get("tipo"),
                "votos_si":      vot["votos_si"],
                "votos_no":      vot["votos_no"],
                "abstenciones":  vot["abstenciones"],
                "pareos":        0,
                "quorum":        vot.get("quorum"),
                "resultado":     vot["resultado"],
            }

            stmt = sqlite_insert(Votacion).values(
                **datos,
                ultima_actualizacion=datetime.now(timezone.utc)
            ).prefix_with("OR IGNORE")
            result = db.execute(stmt)

            if result.rowcount > 0:
                nuevas_boletin += 1
                total_nuevas   += 1
                detalles = obtener_detalle_votacion(vid)
                for d in detalles:
                    db.add(VotoDetalle(
                        votacion_id   = interno_id,
                        parlamentario = d["parlamentario"],
                        seleccion     = d["seleccion"],
                    ))
                time.sleep(PAUSA)

        db.commit()
        if verbose and nuevas_boletin > 0:
            print(f"    {boletin}: +{nuevas_boletin} votaciones ✅")

        time.sleep(PAUSA)

    return total_nuevas


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from database import SessionLocal, engine
    from models import Base, Votacion
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    boletines_prueba = ["18137-05", "16481-25"]
    print("Probando con títulos desde API Senado:\n")
    for b in boletines_prueba:
        titulo = obtener_titulo_boletin(b)
        print(f"  {b}: {titulo[:70] if titulo else 'Sin título'}")
    db.close()
