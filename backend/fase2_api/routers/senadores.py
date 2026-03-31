# ============================================================
# routers/senadores.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Senador

router = APIRouter()


def _serializar(s: Senador) -> dict:
    return {
        "id":               s.id,
        "apellido_paterno": s.apellido_paterno,
        "apellido_materno": s.apellido_materno,
        "nombre":           s.nombre,
        "nombre_completo":  s.nombre_completo,
        "region":           s.region,
        "circunscripcion":  s.circunscripcion,
        "partido":          s.partido,
        "telefono":         s.telefono,
        "email":            s.email,
        "curriculum_url":   s.curriculum_url,
    }


@router.get("/")
def listar_senadores(db: Session = Depends(get_db)):
    senadores = (
        db.query(Senador)
        .order_by(Senador.apellido_paterno)
        .all()
    )
    return {
        "total":    len(senadores),
        "fuente":   "Senado de Chile",
        "senadores": [_serializar(s) for s in senadores],
    }


@router.get("/{senador_id}")
def obtener_senador(senador_id: str, db: Session = Depends(get_db)):
    senador = db.query(Senador).filter(Senador.id == senador_id).first()
    if not senador:
        raise HTTPException(status_code=404, detail=f"No se encontró senador con ID {senador_id}")
    return _serializar(senador)
