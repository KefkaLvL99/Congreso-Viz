# ============================================================
# routers/gastos.py
# ============================================================
# GET /gastos/senadores                → resumen por senador
# GET /gastos/senadores/{senador_id}   → detalle por senador
# GET /gastos/categorias               → categorías disponibles
# ============================================================

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import GastoSenador, Senador

router = APIRouter()


@router.get("/senadores")
def resumen_gastos_senadores(
    db:  Session = Depends(get_db),
    ano: int     = Query(default=None),
):
    """
    Retorna el gasto total por senador, opcionalmente filtrado por año.
    Ordenado de mayor a menor gasto.
    """
    query = db.query(
        GastoSenador.senador_id,
        GastoSenador.appaterno,
        GastoSenador.apmaterno,
        GastoSenador.nombre_api,
        func.sum(GastoSenador.monto).label("total"),
        func.count(GastoSenador.id).label("registros"),
    ).filter(GastoSenador.senador_id != None)

    if ano:
        query = query.filter(GastoSenador.ano == ano)

    resultados = (
        query
        .group_by(GastoSenador.senador_id, GastoSenador.appaterno,
                  GastoSenador.apmaterno, GastoSenador.nombre_api)
        .order_by(func.sum(GastoSenador.monto).desc())
        .all()
    )

    # Enriquecer con datos del senador
    lista = []
    for r in resultados:
        senador = db.query(Senador).filter(Senador.id == r.senador_id).first()
        lista.append({
            "senador_id":     r.senador_id,
            "nombre_completo": senador.nombre_completo if senador else f"{r.nombre_api} {r.appaterno}",
            "partido":        senador.partido if senador else None,
            "region":         senador.region if senador else None,
            "total_gasto":    r.total,
            "registros":      r.registros,
        })

    # Años disponibles
    anios = db.query(func.distinct(GastoSenador.ano))\
              .filter(GastoSenador.senador_id != None)\
              .order_by(GastoSenador.ano.desc()).all()

    return {
        "ano":     ano,
        "total":   len(lista),
        "anios":   [a[0] for a in anios],
        "senadores": lista,
    }


@router.get("/senadores/{senador_id}")
def detalle_gastos_senador(
    senador_id: str,
    db:  Session = Depends(get_db),
    ano: int     = Query(default=None),
):
    """
    Retorna el detalle de gastos de un senador específico.
    Agrupa por categoría y año/mes.
    """
    senador = db.query(Senador).filter(Senador.id == senador_id).first()
    if not senador:
        raise HTTPException(status_code=404, detail="Senador no encontrado")

    query = db.query(GastoSenador).filter(GastoSenador.senador_id == senador_id)
    if ano:
        query = query.filter(GastoSenador.ano == ano)

    gastos = query.order_by(GastoSenador.ano.desc(), GastoSenador.mes.desc()).all()

    if not gastos:
        return {"senador_id": senador_id, "nombre": senador.nombre_completo,
                "gastos": [], "total": 0, "por_categoria": {}}

    # Agrupar por categoría
    por_categoria = {}
    for g in gastos:
        cat = g.categoria
        if cat not in por_categoria:
            por_categoria[cat] = 0
        por_categoria[cat] += g.monto

    # Ordenar por monto desc
    por_categoria = dict(sorted(por_categoria.items(), key=lambda x: x[1], reverse=True))

    # Detalle mensual
    detalle = [
        {
            "ano":       g.ano,
            "mes":       g.mes,
            "categoria": g.categoria,
            "monto":     g.monto,
        }
        for g in gastos
    ]

    anios = sorted(set(g.ano for g in gastos), reverse=True)

    return {
        "senador_id":     senador_id,
        "nombre_completo": senador.nombre_completo,
        "partido":        senador.partido,
        "region":         senador.region,
        "ano":            ano,
        "anios":          anios,
        "total_gasto":    sum(g.monto for g in gastos),
        "por_categoria":  por_categoria,
        "detalle":        detalle,
    }


@router.get("/categorias")
def listar_categorias(db: Session = Depends(get_db)):
    categorias = db.query(func.distinct(GastoSenador.categoria))\
                   .order_by(GastoSenador.categoria).all()
    return {"categorias": [c[0] for c in categorias]}
