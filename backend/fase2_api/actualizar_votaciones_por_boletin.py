# ============================================================
# actualizar_votaciones_por_boletin.py
# ============================================================
# Consulta el endpoint ?fecha=X para obtener boletines en
# tramitación, luego consulta cada uno por ?boletin=X&tipo=Y
# para obtener su historial completo de votaciones.
# ============================================================

import sys
import re
import time
import hashlib
import requests
from lxml import etree
from datetime import datetime, timezone

sys.path.insert(0, ".")
from database import SessionLocal, engine
from models import Base, Votacion, VotoDetalle
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

HEADERS   = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
URL_FECHA = "https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha}"
URL_BOL   = "https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin={num}&tipo={tipo}"
PAUSA     = 0.5
TIMEOUT   = 60


def split_boletin(boletin: str):
    m = re.match(r'^(\d+)-(\d+)$', boletin.strip())
    return (m.group(1), m.group(2)) if m else None


def parsear_votaciones_xml(contenido: bytes, boletin: str) -> list[dict]:
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
            resultado = "Aprobado" if si > no else ("Rechazado" if no > si else "Empate")

            hash_id = hashlib.md5(
                f"{boletin}{sesion}{fecha}{tema[:50]}".encode()
            ).hexdigest()[:8]
            vid = f"{boletin}-{sesion}-{fecha}-{hash_id}".replace("/", "")

            detalles = []
            detalle_nodo = vot.find("DETALLE_VOTACION")
            if detalle_nodo is not None:
                for voto in detalle_nodo.iter("VOTO"):
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
                "resultado":     resultado,
                "detalles":      detalles,
            })

    return votaciones


def guardar_votaciones(votaciones: list[dict], db) -> int:
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
    return nuevas


def obtener_boletines_en_tramitacion(fecha: str) -> list[str]:
    """Obtiene boletines en tramitación desde el endpoint por fecha."""
    url = URL_FECHA.format(fecha=fecha)
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(r.content, parser=parser)
        boletines = []
        for p in root.iter("proyecto"):
            b = p.find("descripcion/boletin")
            e = p.find("descripcion/estado")
            if b is not None and b.text and e is not None:
                estado = e.text or ""
                if "tramitación" in estado or "tramitacion" in estado.lower():
                    boletin = b.text.strip()
                    if re.match(r'^\d+-\d+$', boletin):
                        boletines.append(boletin)
        return boletines
    except Exception as e:
        print(f"  ⚠️  Error obteniendo boletines: {e}")
        return []


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Obtener boletines en tramitación
    from datetime import date, timedelta
    fecha_hoy = date.today().strftime("%d/%m/%Y")
    fecha_30d = (date.today() - timedelta(days=30)).strftime("%d/%m/%Y")

    print("Obteniendo boletines en tramitación...")
    boletines = set()
    for fecha in [fecha_hoy, fecha_30d]:
        nuevos = obtener_boletines_en_tramitacion(fecha)
        boletines.update(nuevos)
        print(f"  fecha={fecha}: {len(nuevos)} boletines")
        time.sleep(1)

    # Agregar también los boletines que ya están en la BD
    from models import Votacion as VotModel
    bols_bd = db.query(VotModel.boletin)\
                .filter(VotModel.camara != "C.Diputados")\
                .filter(VotModel.boletin != None)\
                .distinct().all()
    for (b,) in bols_bd:
        if b and re.match(r'^\d+-\d+$', b):
            boletines.add(b)

    boletines = sorted(boletines)
    print(f"\nTotal boletines a actualizar: {len(boletines)}\n")

    total_nuevas = 0

    for i, boletin in enumerate(boletines):
        partes = split_boletin(boletin)
        if not partes:
            continue

        num, tipo = partes
        url = URL_BOL.format(num=num, tipo=tipo)

        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200 or len(r.content) < 200:
                continue
            if b"No existe" in r.content:
                continue

            votaciones = parsear_votaciones_xml(r.content, boletin)
            nuevas     = guardar_votaciones(votaciones, db)
            total_nuevas += nuevas

            if nuevas > 0:
                print(f"  [{i+1:3d}/{len(boletines)}] {boletin}: +{nuevas} votaciones nuevas ✅")
            elif (i + 1) % 10 == 0:
                print(f"  [{i+1:3d}/{len(boletines)}] procesados...")

        except Exception as e:
            db.rollback()
            print(f"  ⚠️  Error {boletin}: {e}")

        time.sleep(PAUSA)

    db.close()

    print(f"\n✅ Actualización completa")
    print(f"   Boletines procesados: {len(boletines)}")
    print(f"   Votaciones nuevas:    {total_nuevas}")


if __name__ == "__main__":
    main()
