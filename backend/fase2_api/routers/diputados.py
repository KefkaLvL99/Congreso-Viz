# ============================================================
# routers/diputados.py
# ============================================================
# Endpoints de diputados:
#
#   GET /diputados/          → lista todos los diputados
#   GET /diputados/{id}      → detalle de uno específico
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Diputado

router = APIRouter()


@router.get("/")
def listar_diputados(db: Session = Depends(get_db)):
    """
    Retorna la lista completa de diputados vigentes desde la BD.
    Mucho más rápido que el scraping — responde en milisegundos.
    """
    diputados = db.query(Diputado).order_by(Diputado.apellido_paterno).all()

    return {
        "total":      len(diputados),
        "fuente":     "Cámara de Diputadas y Diputados de Chile",
        "diputados": [
            {
                "id":              d.id,
                "nombre_completo": d.nombre_completo,
                "nombre":          d.nombre,
                "apellido_paterno": d.apellido_paterno,
                "region":          d.region,
                "distrito":        d.distrito,
                "periodo":         d.periodo,
                "partido":         d.partido,
                "bancada":         d.bancada,
                "email":           d.email,
                "url_perfil":      d.url_perfil,
                "ultima_actualizacion": d.ultima_actualizacion,
            }
            for d in diputados
        ]
    }


@router.get("/{diputado_id}")
def obtener_diputado(diputado_id: str, db: Session = Depends(get_db)):
    """
    Retorna el detalle de un diputado por su ID.
    """
    d = db.query(Diputado).filter(Diputado.id == diputado_id).first()

    if not d:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró diputado con ID {diputado_id}"
        )

    return {
        "id":              d.id,
        "nombre_completo": d.nombre_completo,
        "nombre":          d.nombre,
        "apellido_paterno": d.apellido_paterno,
        "region":          d.region,
        "distrito":        d.distrito,
        "periodo":         d.periodo,
        "partido":         d.partido,
        "bancada":         d.bancada,
        "email":           d.email,
        "url_perfil":      d.url_perfil,
        "ultima_actualizacion": d.ultima_actualizacion,
    }
