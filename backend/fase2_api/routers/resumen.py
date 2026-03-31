# ============================================================
# routers/resumen.py
# ============================================================

import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import anthropic

from database import get_db
from models import Votacion, ResumenIA

router = APIRouter()


def _construir_contexto(boletin: str, votaciones: list) -> str:
    primera = votaciones[0]
    detalle_vots = []
    for v in votaciones:
        linea = f"- {v.fecha}: {v.tema or v.titulo}"
        linea += f" → {v.resultado} ({v.votos_si} a favor, {v.votos_no} en contra"
        if v.abstenciones:
            linea += f", {v.abstenciones} abstenciones"
        linea += ")"
        if v.tipo_votacion:
            linea += f" [{v.tipo_votacion}]"
        detalle_vots.append(linea)

    return f"""Proyecto de ley chileno:
Título: {primera.titulo}
Boletín: {boletin}
Cámara de origen: {primera.camara}
Estado: {primera.estado or 'En tramitación'}
Etapa actual: {primera.etapa or 'Sin información'}

Votaciones realizadas ({len(votaciones)} en total):
{chr(10).join(detalle_vots)}
"""


def _generar_resumen(contexto: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no está configurada en el entorno")

    cliente = anthropic.Anthropic(api_key=api_key)
    mensaje = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Eres un experto en legislación chilena que explica proyectos de ley a ciudadanos comunes sin conocimientos legales.

Basándote en la siguiente información de un proyecto de ley, genera un resumen claro y accesible que explique:
1. De qué trata este proyecto en términos simples (qué cambia o qué crea)
2. A quién afecta directamente (ciudadanos, empresas, instituciones)
3. Por qué es importante o qué problema busca resolver
4. En qué etapa se encuentra y qué significa eso

El resumen debe ser directo, sin tecnicismos legales, como si se lo explicaras a un amigo. Máximo 4 párrafos cortos. No uses markdown con # ni ##, solo texto plano con párrafos separados.

Información del proyecto:
{contexto}"""
            }
        ]
    )
    return mensaje.content[0].text


@router.get("/{boletin}")
def obtener_resumen(boletin: str, db: Session = Depends(get_db)):
    # Buscar en caché primero
    resumen_cacheado = db.query(ResumenIA).filter(
        ResumenIA.boletin == boletin
    ).first()

    if resumen_cacheado:
        return {
            "boletin":     boletin,
            "resumen":     resumen_cacheado.resumen,
            "generado":    resumen_cacheado.fecha_generacion.isoformat(),
            "desde_cache": True,
        }

    # Obtener votaciones del proyecto
    votaciones = (
        db.query(Votacion)
        .filter(Votacion.boletin == boletin)
        .order_by(desc(Votacion.fecha))
        .all()
    )

    if not votaciones:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron votaciones para boletín {boletin}"
        )

    # Generar resumen con Claude
    try:
        contexto = _construir_contexto(boletin, votaciones)
        resumen  = _generar_resumen(contexto)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar resumen: {str(e)}")

    # Guardar en caché
    try:
        nuevo = ResumenIA(
            boletin = boletin,
            resumen = resumen,
            titulo  = votaciones[0].titulo,
        )
        db.add(nuevo)
        db.commit()
    except Exception:
        db.rollback()
        existente = db.query(ResumenIA).filter(ResumenIA.boletin == boletin).first()
        if existente:
            resumen = existente.resumen

    return {
        "boletin":     boletin,
        "resumen":     resumen,
        "desde_cache": False,
    }
