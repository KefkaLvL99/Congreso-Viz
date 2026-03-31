# ============================================================
# scraper_tramitacion_senado.py
# ============================================================
# Scrapea la página de tramitación del Senado para obtener
# boletines activos y sus votaciones históricas.
# ============================================================

import re
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from lxml import etree
from datetime import datetime, timezone

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
URL_TRAM = "https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php"
URL_BOL  = "https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin={num}&tipo={tipo}"
TIMEOUT  = 60
PAUSA    = 0.4


def obtener_boletines_desde_pagina() -> list[dict]:
    """
    Scrapea la página de tramitación y retorna todos los boletines
    de las tablas PIniciados y PLDespachados.
    """
    r = requests.get(URL_TRAM, headers=HEADERS, timeout=TIMEOUT)
    soup = BeautifulSoup(r.content, "html.parser")

    boletines = []
    tablas_objetivo = ["PIniciados", "PLDespachados"]

    for tabla_id in tablas_objetivo:
        tabla = soup.find("table", {"id": tabla_id})
        if not tabla:
            continue

        for fila in tabla.find_all("tr"):
            celdas = [td.get_text(strip=True) for td in fila.find_all(["td", "th"])]
            if len(celdas) < 4:
                continue
            boletin = celdas[0].strip()
            if not re.match(r'^\d+-\d+$', boletin):
                continue

            titulo = celdas[1].strip() if len(celdas) > 1 else ""
            ley    = celdas[2].strip() if len(celdas) > 2 else ""
            estado = celdas[3].strip() if len(celdas) > 3 else ""
            fecha  = celdas[4].strip() if len(celdas) > 4 else ""

            boletines.append({
                "boletin": boletin,
                "titulo":  titulo,
                "ley":     ley,
                "estado":  estado,
                "fecha":   fecha,
                "tabla":   tabla_id,
            })

    # Deduplicar
    vistos = set()
    unicos = []
    for b in boletines:
        if b["boletin"] not in vistos:
            vistos.add(b["boletin"])
            unicos.append(b)

    return unicos


def parsear_votaciones_boletin(contenido: bytes, boletin: str) -> list[dict]:
    """Parsea el XML de un boletín y retorna sus votaciones."""
    parser = etree.XMLParser(recover=True)
    try:
        root = etree.fromstring(contenido, parser=parser)
    except Exception:
        return []

    votaciones = []
    for proyecto in root.iter("proyecto"):
        def cp(tag):
            e = proyecto.find(f"descripcion/{tag}")
            return e.text.strip() if e is not None and e.text else None

        titulo = cp("titulo")
        camara = cp("camara_origen")
        estado = cp("estado")

        nodo_vots = proyecto.find("votaciones")
        if nodo_vots is None:
            continue

        for vot in nodo_vots.iter("votacion"):
            def cv(tag):
                e = vot.find(tag)
                return e.text.strip() if e is not None and e.text else None

            sesion = cv("SESION") or ""
            fecha  = cv("FECHA") or ""
            tema   = cv("TEMA") or ""
            if not fecha:
                continue


            si   = int(cv("SI")   or 0)
            no   = int(cv("NO")   or 0)
            abs_ = int(cv("ABSTENCION") or 0)
            res  = "Aprobado" if si > no else ("Rechazado" if no > si else "Empate")

            hid = hashlib.md5(
                f"{boletin}{sesion}{fecha}{tema[:50]}".encode()
            ).hexdigest()[:8]
            vid = f"{boletin}-{sesion}-{fecha}-{hid}".replace("/", "")

            detalles = []
            dn = vot.find("DETALLE_VOTACION")
            if dn is not None:
                for voto in dn.iter("VOTO"):
                    parl = voto.find("PARLAMENTARIO")
                    sel  = voto.find("SELECCION")
                    if parl is not None and parl.text and sel is not None and sel.text:
                        detalles.append({
                            "parlamentario": parl.text.strip(),
                            "seleccion":     sel.text.strip(),
                        })

            votaciones.append({
                "id":            vid,
                "boletin":       boletin,
                "titulo":        titulo,
                "camara":        camara or "Senado",
                "etapa":         cv("ETAPA"),
                "estado":        estado,
                "sesion":        sesion,
                "fecha":         fecha,
                "tema":          tema,
                "tipo_votacion": cv("TIPOVOTACION"),
                "votos_si":      si,
                "votos_no":      no,
                "abstenciones":  abs_,
                "pareos":        int(cv("PAREO") or 0),
                "quorum":        cv("QUORUM"),
                "resultado":     res,
                "detalles":      detalles,
            })

    return votaciones


def sincronizar_votaciones_senado(db, verbose=True) -> int:
    """
    Función principal — obtiene boletines activos y sincroniza
    sus votaciones desde 2020 hasta hoy.
    Retorna cantidad de votaciones nuevas.
    """
    from models import Votacion, VotoDetalle
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    if verbose:
        print("  → Scraping boletines activos del Senado...")

    boletines = obtener_boletines_desde_pagina()
    if verbose:
        print(f"    Boletines encontrados: {len(boletines)}")

    total_nuevas = 0

    for info in boletines:
        boletin = info["boletin"]
        num, tipo = boletin.split("-")

        try:
            r = requests.get(
                URL_BOL.format(num=num, tipo=tipo),
                headers=HEADERS, timeout=TIMEOUT
            )
            if r.status_code != 200 or len(r.content) < 200:
                continue
            if b"No existe" in r.content:
                continue

            votaciones = parsear_votaciones_boletin(r.content, boletin)
            nuevas = 0

            for datos in votaciones:
                detalles = datos.pop("detalles", [])
                stmt = sqlite_insert(Votacion).values(
                    **datos,
                    ultima_actualizacion=datetime.now(timezone.utc)
                ).prefix_with("OR IGNORE")
                result = db.execute(stmt)
                if result.rowcount > 0:
                    nuevas += 1
                    for d in detalles:
                        db.add(VotoDetalle(
                            votacion_id   = datos["id"],
                            parlamentario = d["parlamentario"],
                            seleccion     = d["seleccion"],
                        ))

            db.commit()
            total_nuevas += nuevas

            if verbose and nuevas > 0:
                print(f"    {boletin} ({info['estado']}): +{nuevas} votaciones ✅")

            time.sleep(PAUSA)

        except Exception as e:
            db.rollback()
            if verbose:
                print(f"    ⚠️  Error {boletin}: {e}")

    return total_nuevas


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from database import SessionLocal, engine
    from models import Base
    from sqlalchemy import func
    from models import Votacion

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=" * 60)
    print("Sincronización votaciones Senado desde página de tramitación")
    print("=" * 60)

    antes = db.query(func.count(Votacion.id)).filter(
        Votacion.camara != "C.Diputados"
    ).scalar()

    nuevas = sincronizar_votaciones_senado(db, verbose=True)

    despues = db.query(func.count(Votacion.id)).filter(
        Votacion.camara != "C.Diputados"
    ).scalar()

    db.close()
    print(f"\n✅ Votaciones Senado: {antes} → {despues} (+{nuevas} nuevas)")
