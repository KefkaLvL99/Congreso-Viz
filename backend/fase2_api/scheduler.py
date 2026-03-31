# ============================================================
# scheduler.py - Actualización automática de datos
# ============================================================

import requests
import hashlib
import time
from lxml import etree
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from database import SessionLocal, engine
from models import Base, Senador, Comision, ComisionMiembro, Diputado, Votacion, VotoDetalle
from scraper_diputados import obtener_diputados
from scraper_senadores_web import obtener_senadores_web
from scraper_votaciones_camara import obtener_votaciones_recientes_camara
from scraper_tramitacion_senado import sincronizar_votaciones_senado
from scraper_votaciones_camara_ws import sincronizar_camara_por_boletines

URL_COMISIONES  = "https://tramitacion.senado.cl/wspublico/comisiones.php"
URL_TRAMITACION = "https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha}"
TIMEOUT = 15


def _horas_desde(db, modelo, filtro=None) -> float:
    q = db.query(modelo.ultima_actualizacion)
    if filtro is not None:
        q = q.filter(filtro)
    ultimo = q.order_by(modelo.ultima_actualizacion.desc()).first()
    if not ultimo or not ultimo[0]:
        return 999
    ts = ultimo[0]
    if hasattr(ts, 'tzinfo') and ts.tzinfo is None:
        from datetime import timezone as tz
        now = datetime.utcnow()
    else:
        now = datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    delta = now - ts
    return delta.total_seconds() / 3600


def parsear_comisiones(contenido_xml: bytes) -> list[dict]:
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(contenido_xml, parser=parser)
    comisiones = []
    for nodo in root.iter("comision"):
        def campo(tag):
            e = nodo.find(tag)
            return e.text.strip() if e is not None and e.text else None
        miembros = []
        nodo_integrantes = nodo.find("integrantes")
        if nodo_integrantes is not None:
            for integrante in nodo_integrantes.iter("integrante"):
                def campo_i(tag):
                    e = integrante.find(tag)
                    return e.text.strip() if e is not None and e.text else None
                miembros.append({
                    "senador_id": campo_i("PARLID"),
                    "cargo":      campo_i("CARGO"),
                    "funcion":    campo_i("FUNCION"),
                    "saludo":     campo_i("SALUDO"),
                })
        comisiones.append({
            "id":       campo("id"),
            "nombre":   campo("nombre"),
            "tipo":     campo("tipo"),
            "email":    campo("email"),
            "miembros": miembros,
        })
    return comisiones


def parsear_votaciones_senado(contenido_xml: bytes) -> list[dict]:
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(contenido_xml, parser=parser)
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
            si   = int(cv("SI")  or 0)
            no   = int(cv("NO")  or 0)
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
                "id": vid, "boletin": boletin, "titulo": titulo,
                "camara": camara or "Senado", "etapa": cv("ETAPA"),
                "estado": estado, "sesion": sesion, "fecha": fecha,
                "tema": tema, "tipo_votacion": cv("TIPOVOTACION"),
                "votos_si": si, "votos_no": no, "abstenciones": abs_,
                "pareos": int(cv("PAREO") or 0), "quorum": cv("QUORUM"),
                "resultado": resultado, "detalles": detalles,
            })
    return votaciones


def _guardar_votaciones(votaciones: list[dict], db: Session) -> int:
    total_nuevas = 0
    for datos in votaciones:
        if not datos.get("id"):
            continue
        detalles = datos.pop("detalles", [])
        stmt = sqlite_insert(Votacion).values(
            **datos,
            ultima_actualizacion=datetime.now(timezone.utc)
        ).prefix_with("OR IGNORE")
        result = db.execute(stmt)
        if result.rowcount > 0:
            total_nuevas += 1
            for d in detalles:
                db.add(VotoDetalle(
                    votacion_id   = datos["id"],
                    parlamentario = d["parlamentario"],
                    seleccion     = d["seleccion"],
                ))
    db.commit()
    return total_nuevas


def _obtener_boletines_activos() -> list[str]:
    """Obtiene boletines activos desde la página de tramitación del Senado."""
    from scraper_tramitacion_senado import obtener_boletines_desde_pagina
    try:
        boletines_info = obtener_boletines_desde_pagina()
        return [b["boletin"] for b in boletines_info]
    except Exception:
        return []


def sincronizar():
    print(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Iniciando sincronización...")
    db: Session = SessionLocal()

    try:
        # ── SENADORES ─────────────────────────────────────────
        horas_sen = _horas_desde(db, Senador)
        if horas_sen > 12:
            senadores_web = obtener_senadores_web(verbose=True)
            for datos in senadores_web:
                if not datos["id"]:
                    continue
                existente = db.query(Senador).filter(
                    Senador.nombre_completo == datos["nombre_completo"]
                ).first()
                if existente:
                    for k, v in datos.items():
                        if v is not None:
                            setattr(existente, k, v)
                    existente.ultima_actualizacion = datetime.utcnow()
                else:
                    db.add(Senador(**datos, ultima_actualizacion=datetime.utcnow()))
            db.commit()
            print(f"  ✅ Senadores sincronizados: {len(senadores_web)}")
        else:
            print(f"  ⏭️  Senadores omitidos — sincronizados hace {horas_sen:.1f}h")

        # ── COMISIONES ────────────────────────────────────────
        if horas_sen > 12:
            print("  → Consultando comisiones...")
            r = requests.get(URL_COMISIONES, timeout=TIMEOUT)
            r.raise_for_status()
            comisiones = parsear_comisiones(r.content)
            for datos in comisiones:
                if not datos["id"]:
                    continue
                comision = db.query(Comision).filter(Comision.id == datos["id"]).first()
                if comision:
                    comision.nombre = datos["nombre"]
                    comision.tipo   = datos["tipo"]
                    comision.email  = datos["email"]
                    comision.ultima_actualizacion = datetime.utcnow()
                else:
                    db.add(Comision(
                        id=datos["id"], nombre=datos["nombre"],
                        tipo=datos["tipo"], email=datos["email"],
                        ultima_actualizacion=datetime.utcnow(),
                    ))
                db.commit()
                db.query(ComisionMiembro).filter(
                    ComisionMiembro.comision_id == datos["id"]
                ).delete()
                for m in datos["miembros"]:
                    if not m["senador_id"]:
                        continue
                    db.add(ComisionMiembro(
                        senador_id=m["senador_id"], comision_id=datos["id"],
                        cargo=m["cargo"], funcion=m["funcion"], saludo=m["saludo"],
                        ultima_actualizacion=datetime.utcnow(),
                    ))
                db.commit()
            print(f"  ✅ Comisiones sincronizadas: {len(comisiones)}")
        else:
            print(f"  ⏭️  Comisiones omitidas — sincronizadas hace {horas_sen:.1f}h")

        # ── DIPUTADOS ─────────────────────────────────────────
        horas_dip = _horas_desde(db, Diputado)
        if horas_dip > 24:
            print("  → Scraping diputados (~2 minutos)...")
            diputados = obtener_diputados(verbose=False)
            for datos in diputados:
                if not datos["id"]:
                    continue
                diputado = db.query(Diputado).filter(Diputado.id == datos["id"]).first()
                if diputado:
                    for k, v in datos.items():
                        setattr(diputado, k, v)
                    diputado.ultima_actualizacion = datetime.utcnow()
                else:
                    db.add(Diputado(**datos, ultima_actualizacion=datetime.utcnow()))
            db.commit()
            print(f"  ✅ Diputados sincronizados: {len(diputados)}")
        else:
            print(f"  ⏭️  Diputados omitidos — sincronizados hace {horas_dip:.1f}h")

        # ── VOTACIONES SENADO por fecha ───────────────────────
        print("  → Consultando votaciones Senado (últimos 30 días)...")
        total_senado = 0
        for dias_atras in [7, 14, 21, 30]:
            fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%d/%m/%Y")
            url   = URL_TRAMITACION.format(fecha=fecha)
            for intento in range(3):
                try:
                    r = requests.get(url, timeout=120)
                    r.raise_for_status()
                    votaciones = parsear_votaciones_senado(r.content)
                    total_senado += _guardar_votaciones(votaciones, db)
                    break
                except Exception as e:
                    if intento < 2:
                        print(f"    ⚠️  Reintento {intento+1}/3 fecha -{dias_atras}d: {e}")
                        time.sleep(5)
                    else:
                        db.rollback()
                        print(f"    ❌ Falló fecha -{dias_atras}d después de 3 intentos")
        print(f"  ✅ Votaciones Senado (por fecha) nuevas: {total_senado}")

        # ── VOTACIONES SENADO por boletín ─────────────────────
        print("  → Actualizando boletines activos del Senado...")
        total_sen_bol = sincronizar_votaciones_senado(db, verbose=False)
        print(f"  ✅ Votaciones Senado (por boletín) nuevas: {total_sen_bol}")

        # ── VOTACIONES CÁMARA por boletín (webservice) ────────
        print("  → Actualizando votaciones Cámara por boletín...")
        boletines = _obtener_boletines_activos()
        # Agregar boletines ya en BD de la Cámara
        bols_bd = db.query(Votacion.boletin)\
                    .filter(Votacion.camara == "C.Diputados")\
                    .filter(Votacion.boletin != None)\
                    .distinct().all()
        import re
        for (b,) in bols_bd:
            if b and re.match(r'^\d+-\d+$', b) and b not in boletines:
                boletines.append(b)
        total_cam_bol = sincronizar_camara_por_boletines(boletines, db, verbose=False)
        print(f"  ✅ Votaciones Cámara (por boletín) nuevas: {total_cam_bol}")

        # ── VOTACIONES CÁMARA por IDs recientes ───────────────
        horas_cam = _horas_desde(db, Votacion,
                                  filtro=(Votacion.camara == "C.Diputados"))
        if horas_cam > 6:
            print("  → Scraping votaciones Cámara (últimas 100 por ID)...")
            try:
                votaciones_camara = obtener_votaciones_recientes_camara(
                    cantidad=100, verbose=False
                )
                total_cam_ids = _guardar_votaciones(votaciones_camara, db)
                print(f"  ✅ Votaciones Cámara (por ID) nuevas: {total_cam_ids}")
            except Exception as e:
                db.rollback()
                print(f"  ⚠️  Error votaciones Cámara por ID: {e}")
        else:
            print(f"  ⏭️  Votaciones Cámara por ID omitidas — hace {horas_cam:.1f}h")

        print(f"  ✅ Sincronización completada.\n")

    except Exception as e:
        print(f"  ❌ Error durante sincronización: {e}")
        db.rollback()
    finally:
        db.close()


def iniciar_scheduler():
    print("  Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("  ✅ Tablas listas.")

    sincronizar()

    scheduler = BackgroundScheduler()
    scheduler.add_job(sincronizar, trigger="interval", hours=6, id="sync_congreso")
    scheduler.start()
    print("  ✅ Scheduler iniciado — sincronización cada 6 horas.\n")

    return scheduler
