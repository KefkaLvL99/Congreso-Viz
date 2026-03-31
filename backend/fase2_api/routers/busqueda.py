# ============================================================
# routers/busqueda.py
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Senador, Diputado

router = APIRouter()


def _normalizar(texto: str) -> str:
    return texto.replace(".", "").replace(" ", "").lower()


def _nombre_a_xml(nombre_completo, apellido_paterno, apellido_materno) -> str:
    if not nombre_completo or not apellido_paterno:
        return nombre_completo or ""
    partes = nombre_completo.split()
    nombre = " ".join(partes[:-2]) if len(partes) >= 3 else (partes[0] if partes else "")
    inicial_m = apellido_materno[0] + "." if apellido_materno else ""
    return f"{apellido_paterno} {inicial_m}, {nombre}".strip()


def _serializar_senador(s: Senador) -> dict:
    nombre_xml = _nombre_a_xml(s.nombre_completo, s.apellido_paterno, s.apellido_materno)
    return {
        "nombre_completo": s.nombre_completo,
        "nombre_xml":      nombre_xml,
        "partido":         s.partido,
        "region":          s.region,
        "camara":          "Senado",
        "territorio":      f"Circunscripción {s.circunscripcion}" if s.circunscripcion else None,
    }


def _serializar_diputado(d: Diputado) -> dict:
    partes = d.nombre_completo.split() if d.nombre_completo else []
    apellido_materno = partes[-1] if len(partes) >= 3 else ""
    nombre_xml = _nombre_a_xml(d.nombre_completo, d.apellido_paterno, apellido_materno)
    return {
        "nombre_completo": d.nombre_completo,
        "nombre_xml":      nombre_xml,
        "partido":         d.partido,
        "region":          d.region,
        "camara":          "Cámara de Diputados",
        "territorio":      d.distrito,
    }


@router.get("/")
def buscar_parlamentarios(
    q:    str = Query(default="", min_length=1),
    modo: str = Query(default="nombre"),
    db:   Session = Depends(get_db),
):
    if not q or len(q.strip()) < 2:
        return {"total": 0, "resultados": []}

    termino  = f"%{q.strip()}%"
    q_norm   = _normalizar(q.strip())
    resultados = []
    vistos   = set()

    # ── MODO NOMBRE ──────────────────────────────────────────
    if modo == "nombre":
        senadores = (
            db.query(Senador)
            .filter(
                or_(
                    Senador.nombre_completo.ilike(termino),
                    Senador.apellido_paterno.ilike(termino),
                    Senador.nombre.ilike(termino),
                )
            )
            .order_by(Senador.apellido_paterno)
            .all()
        )
        for s in senadores:
            if s.nombre_completo not in vistos:
                resultados.append(_serializar_senador(s))
                vistos.add(s.nombre_completo)

        diputados = (
            db.query(Diputado)
            .filter(
                or_(
                    Diputado.nombre_completo.ilike(termino),
                    Diputado.apellido_paterno.ilike(termino),
                    Diputado.nombre.ilike(termino),
                )
            )
            .order_by(Diputado.apellido_paterno)
            .all()
        )
        for d in diputados:
            if d.nombre_completo not in vistos:
                resultados.append(_serializar_diputado(d))
                vistos.add(d.nombre_completo)

    # ── MODO PARTIDO ─────────────────────────────────────────
    elif modo == "partido":
        # Buscar por ilike directo
        senadores = db.query(Senador).filter(Senador.partido.ilike(termino)).all()
        for s in senadores:
            if s.nombre_completo not in vistos:
                resultados.append(_serializar_senador(s))
                vistos.add(s.nombre_completo)

        diputados = db.query(Diputado).filter(
            or_(Diputado.partido.ilike(termino), Diputado.bancada.ilike(termino))
        ).all()
        for d in diputados:
            if d.nombre_completo not in vistos:
                resultados.append(_serializar_diputado(d))
                vistos.add(d.nombre_completo)

        # Buscar también por partido normalizado (RN → R.N., udi → U.D.I.)
        todos_sen = db.query(Senador).all()
        for s in todos_sen:
            if s.nombre_completo not in vistos and s.partido:
                if q_norm in _normalizar(s.partido):
                    resultados.append(_serializar_senador(s))
                    vistos.add(s.nombre_completo)

        todos_dip = db.query(Diputado).all()
        for d in todos_dip:
            if d.nombre_completo not in vistos:
                partido_norm = _normalizar(d.partido or "")
                bancada_norm = _normalizar(d.bancada or "")
                if q_norm in partido_norm or q_norm in bancada_norm:
                    resultados.append(_serializar_diputado(d))
                    vistos.add(d.nombre_completo)

    # ── MODO REGIÓN ──────────────────────────────────────────
    elif modo == "region":
        senadores = (
            db.query(Senador)
            .filter(Senador.region.ilike(termino))
            .order_by(Senador.apellido_paterno)
            .all()
        )
        for s in senadores:
            if s.nombre_completo not in vistos:
                resultados.append(_serializar_senador(s))
                vistos.add(s.nombre_completo)

        diputados = (
            db.query(Diputado)
            .filter(Diputado.region.ilike(termino))
            .order_by(Diputado.apellido_paterno)
            .all()
        )
        for d in diputados:
            if d.nombre_completo not in vistos:
                resultados.append(_serializar_diputado(d))
                vistos.add(d.nombre_completo)

    # Ordenar por apellido
    resultados.sort(key=lambda x: x["nombre_completo"] or "")

    return {
        "total":      len(resultados),
        "query":      q,
        "modo":       modo,
        "resultados": resultados,
    }
