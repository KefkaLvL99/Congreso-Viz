# ============================================================
# routers/votaciones.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database import get_db
from models import Votacion, VotoDetalle

router = APIRouter()


def _serializar(v: Votacion) -> dict:
    return {
        "id":            v.id,
        "boletin":       v.boletin,
        "titulo":        v.titulo,
        "camara":        v.camara,
        "etapa":         v.etapa,
        "estado":        v.estado,
        "sesion":        v.sesion,
        "fecha":         v.fecha,
        "tema":          v.tema,
        "tipo_votacion": v.tipo_votacion,
        "votos_si":      v.votos_si,
        "votos_no":      v.votos_no,
        "abstenciones":  v.abstenciones,
        "resultado":     v.resultado,
        "quorum":        v.quorum,
        "tiene_detalle": len(v.detalles) > 0,
    }


@router.get("/recientes")
def votaciones_recientes(db: Session = Depends(get_db)):
    votaciones = (
        db.query(Votacion)
        .order_by(desc(Votacion.fecha), desc(Votacion.ultima_actualizacion))
        .limit(10)
        .all()
    )
    return {"votaciones": [_serializar(v) for v in votaciones]}


@router.get("/anios")
def anios_disponibles(db: Session = Depends(get_db)):
    votaciones = db.query(Votacion.fecha).all()
    anios = set()
    for (fecha,) in votaciones:
        if fecha and len(fecha) >= 10:
            anio = fecha[-4:]
            if anio.isdigit():
                anios.add(int(anio))
    return {"total": len(anios), "anios": sorted(anios, reverse=True)}


@router.get("/agrupadas")
def votaciones_agrupadas(
    db:     Session = Depends(get_db),
    anio:   int     = Query(default=None),
    camara: str     = Query(default=None),
    limite: int     = Query(default=30, le=100),
    offset: int     = Query(default=0),
    tramitacion: bool = Query(default=False),
):
    """
    Retorna votaciones agrupadas por proyecto (boletín).
    Cada proyecto muestra todas sus votaciones individuales.
    """
    # Filtros base
    def aplicar_filtros(q):
        if anio:
            q = q.filter(Votacion.fecha.like(f"%/{anio}"))
        if camara:
            q = q.filter(Votacion.camara.ilike(f"%{camara}%"))
        if tramitacion:
            q = q.filter(Votacion.estado == "En tramitación")
        return q

    # Boletines únicos con fecha más reciente y conteo
    subq = aplicar_filtros(
        db.query(
            Votacion.boletin,
            func.max(Votacion.fecha).label("fecha_reciente"),
            func.count(Votacion.id).label("total"),
        )
    ).group_by(Votacion.boletin) \
     .order_by(func.max(Votacion.fecha).desc()) \
     .offset(offset) \
     .limit(limite) \
     .all()

    total_proyectos = aplicar_filtros(
        db.query(func.count(func.distinct(Votacion.boletin)))
    ).scalar()

    proyectos = []
    for row in subq:
        vots = aplicar_filtros(
            db.query(Votacion).filter(Votacion.boletin == row.boletin)
        ).order_by(desc(Votacion.fecha)).all()

        if not vots:
            continue

        primera = vots[0]
        proyectos.append({
            "boletin":          row.boletin,
            "titulo":           primera.titulo,
            "camara":           primera.camara,
            "estado":           primera.estado,
            "total_votaciones": row.total,
            "ultima_fecha":     row.fecha_reciente,
            "votaciones": [
                {
                    "id":            v.id,
                    "fecha":         v.fecha,
                    "tema":          v.tema,
                    "tipo_votacion": v.tipo_votacion,
                    "resultado":     v.resultado,
                    "votos_si":      v.votos_si,
                    "votos_no":      v.votos_no,
                    "abstenciones":  v.abstenciones,
                    "tiene_detalle": len(v.detalles) > 0,
                }
                for v in vots
            ],
        })

    return {
        "total_proyectos": total_proyectos,
        "limite":          limite,
        "offset":          offset,
        "anio":            anio,
        "proyectos":       proyectos,
    }


@router.get("/")
def listar_votaciones(
    db:     Session = Depends(get_db),
    limite: int     = Query(default=20, le=100),
    offset: int     = Query(default=0),
    camara: str     = Query(default=None),
    anio:   int     = Query(default=None),
):
    query = db.query(Votacion)
    if camara:
        query = query.filter(Votacion.camara.ilike(f"%{camara}%"))
    if anio:
        query = query.filter(Votacion.fecha.like(f"%/{anio}"))
    total = query.count()
    votaciones = (
        query
        .order_by(desc(Votacion.fecha), desc(Votacion.ultima_actualizacion))
        .offset(offset)
        .limit(limite)
        .all()
    )
    return {
        "total":      total,
        "limite":     limite,
        "offset":     offset,
        "anio":       anio,
        "votaciones": [_serializar(v) for v in votaciones],
    }


@router.get("/{votacion_id}/detalle")
def detalle_votacion(votacion_id: str, db: Session = Depends(get_db)):
    votacion = db.query(Votacion).filter(Votacion.id == votacion_id).first()
    if not votacion:
        raise HTTPException(status_code=404, detail=f"Votación {votacion_id} no encontrada")

    detalles = (
        db.query(VotoDetalle)
        .filter(VotoDetalle.votacion_id == votacion_id)
        .order_by(VotoDetalle.seleccion, VotoDetalle.parlamentario)
        .all()
    )

    grupos = {"Si": [], "No": [], "Abstencion": [], "Pareo": [], "Otro": []}
    for d in detalles:
        grupos[d.seleccion if d.seleccion in grupos else "Otro"].append(d.parlamentario)

    return {
        "votacion_id":     votacion_id,
        "boletin":         votacion.boletin,
        "titulo":          votacion.titulo,
        "fecha":           votacion.fecha,
        "resultado":       votacion.resultado,
        "votos_si":        votacion.votos_si,
        "votos_no":        votacion.votos_no,
        "abstenciones":    votacion.abstenciones,
        "total_registros": len(detalles),
        "detalle": {
            "si":         grupos["Si"],
            "no":         grupos["No"],
            "abstencion": grupos["Abstencion"],
            "pareo":      grupos["Pareo"],
        }
    }


@router.get("/boletin/{boletin}")
def votaciones_por_boletin(boletin: str, db: Session = Depends(get_db)):
    boletin_base = boletin.split("-")[0]
    votaciones = (
        db.query(Votacion)
        .filter(Votacion.boletin.like(f"{boletin_base}%"))
        .order_by(desc(Votacion.fecha))
        .all()
    )
    if not votaciones:
        raise HTTPException(status_code=404, detail=f"No se encontraron votaciones para boletín {boletin}")
    return {
        "boletin":    boletin,
        "titulo":     votaciones[0].titulo,
        "total":      len(votaciones),
        "votaciones": [_serializar(v) for v in votaciones],
    }
