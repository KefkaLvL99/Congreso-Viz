# ============================================================
# cargar_historico_senado.py
# ============================================================
# Script de carga masiva de votaciones históricas del Senado.
# Itera mes a mes desde 2012 hasta hoy.
#
# Características:
# - Reanudable: INSERT OR IGNORE evita duplicados
# - Guarda progreso en un archivo .progress para retomar
# - Tolerante a fallos de red: reintenta 3 veces por mes
# - Muestra progreso en tiempo real
#
# Uso:
#   cd backend/fase2_api
#   source senado/bin/activate
#   python cargar_historico_senado.py
# ============================================================

import sys
import time
import hashlib
import requests
import json
import os
from lxml import etree
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

sys.path.insert(0, ".")
from database import SessionLocal, engine
from models import Base, Votacion, VotoDetalle

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
URL_BASE = "https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha}"
TIMEOUT  = 30
PAUSA    = 1.0      # segundos entre requests
REINTENTOS = 3
PROGRESS_FILE = "historico_senado.progress"

FECHA_INICIO = date(2012, 1, 1)
FECHA_FIN    = date.today()


# ── PROGRESO ─────────────────────────────────────────────────

def cargar_progreso() -> str | None:
    """Retorna el último mes procesado exitosamente."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return f.read().strip()
    return None


def guardar_progreso(mes_str: str):
    with open(PROGRESS_FILE, "w") as f:
        f.write(mes_str)


# ── PARSEO XML ────────────────────────────────────────────────

def parsear_votaciones(contenido_xml: bytes) -> list[dict]:
    parser = etree.XMLParser(recover=True)
    try:
        root = etree.fromstring(contenido_xml, parser=parser)
    except Exception:
        return []

    votaciones = []
    for proyecto in root.iter("proyecto"):
        def cp(tag):
            e = proyecto.find(f"descripcion/{tag}")
            return e.text.strip() if e is not None and e.text else None

        boletin = cp("boletin")
        titulo  = cp("titulo")
        camara  = cp("camara_origen")
        estado  = cp("estado")

        if not boletin:
            continue

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

            contenido_hash = hashlib.md5(
                f"{boletin}{sesion}{fecha}{tema[:50]}".encode()
            ).hexdigest()[:8]
            vid = f"{boletin}-{sesion}-{fecha}-{contenido_hash}".replace("/", "")

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


# ── GUARDAR EN BD ─────────────────────────────────────────────

def guardar_votaciones(votaciones: list[dict], db) -> int:
    nuevas = 0
    for datos in votaciones:
        if not datos.get("id"):
            continue
        detalles = datos.pop("detalles", [])
        stmt = sqlite_insert(Votacion).values(
            **datos,
            ultima_actualizacion=datetime.utcnow()
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


# ── CONSULTAR UN MES ──────────────────────────────────────────

def consultar_mes(fecha_str: str) -> list[dict] | None:
    """Consulta un mes con reintentos. Retorna None si falla."""
    url = URL_BASE.format(fecha=fecha_str)
    for intento in range(REINTENTOS):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return parsear_votaciones(r.content)
        except Exception as e:
            if intento < REINTENTOS - 1:
                print(f"      ⚠️  Reintento {intento+1}/{REINTENTOS}: {e}")
                time.sleep(3)
            else:
                print(f"      ❌ Falló después de {REINTENTOS} intentos: {e}")
                return None


# ── MAIN ──────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Carga histórica de votaciones del Senado")
    print(f"Período: {FECHA_INICIO.strftime('%B %Y')} → {FECHA_FIN.strftime('%B %Y')}")
    print("=" * 60)

    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Generar lista de meses
    meses = []
    fecha_actual = FECHA_INICIO
    while fecha_actual <= FECHA_FIN:
        meses.append(fecha_actual)
        fecha_actual += relativedelta(months=1)

    total_meses = len(meses)
    print(f"Total de meses a procesar: {total_meses}\n")

    # Verificar progreso previo
    ultimo_procesado = cargar_progreso()
    inicio_idx = 0
    if ultimo_procesado:
        for i, m in enumerate(meses):
            if m.strftime("%Y-%m") == ultimo_procesado:
                inicio_idx = i + 1
                break
        if inicio_idx > 0:
            print(f"Retomando desde mes {inicio_idx + 1}/{total_meses} "
                  f"({meses[inicio_idx].strftime('%B %Y') if inicio_idx < total_meses else 'finalizado'})\n")

    # Estadísticas
    total_votaciones  = 0
    total_nuevas      = 0
    meses_con_error   = []

    start_time = time.time()

    for i, mes in enumerate(meses[inicio_idx:], start=inicio_idx):
        # Usar el primer día del mes como fecha de consulta
        fecha_str = mes.strftime("%d/%m/%Y").replace(
            mes.strftime("%d"), "01"
        )

        porcentaje = ((i + 1) / total_meses) * 100
        print(f"[{i+1:3d}/{total_meses}] {mes.strftime('%B %Y'):15s} "
              f"({porcentaje:5.1f}%) ", end="", flush=True)

        votaciones = consultar_mes(fecha_str)

        if votaciones is None:
            meses_con_error.append(mes.strftime("%Y-%m"))
            print("❌ Error")
            continue

        nuevas = guardar_votaciones(votaciones, db)
        total_votaciones += len(votaciones)
        total_nuevas     += nuevas

        # Calcular tiempo estimado restante
        elapsed   = time.time() - start_time
        procesados = i - inicio_idx + 1
        restantes  = total_meses - i - 1
        eta_seg    = (elapsed / procesados) * restantes if procesados > 0 else 0
        eta_min    = eta_seg / 60

        print(f"→ {len(votaciones):3d} votaciones ({nuevas} nuevas) | "
              f"ETA: {eta_min:.1f} min")

        guardar_progreso(mes.strftime("%Y-%m"))
        time.sleep(PAUSA)

    # Resumen final
    elapsed_total = (time.time() - start_time) / 60
    print("\n" + "=" * 60)
    print("CARGA COMPLETADA")
    print(f"  Tiempo total     : {elapsed_total:.1f} minutos")
    print(f"  Votaciones vistas: {total_votaciones}")
    print(f"  Nuevas guardadas : {total_nuevas}")
    print(f"  Meses con error  : {len(meses_con_error)}")
    if meses_con_error:
        print(f"  Meses fallidos   : {', '.join(meses_con_error)}")
    print("=" * 60)

    # Limpiar archivo de progreso si completó
    if not meses_con_error and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("\n✅ Archivo de progreso eliminado — carga completa.")

    db.close()


if __name__ == "__main__":
    main()
