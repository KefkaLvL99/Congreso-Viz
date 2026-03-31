# ============================================================
# routers/leyes.py
# ============================================================

import os
import requests
from lxml import etree
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import ResumenIA
from datetime import datetime, timezone
from pydantic import BaseModel

router = APIRouter()

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
URL_BASE = "https://www.leychile.cl/Consulta/obtxml?opt=3&cantidad={cantidad}"
TIMEOUT  = 15


def _parsear_norma(norma) -> dict:
    def campo(tag):
        e = norma.find(tag)
        return e.text.strip() if e is not None and e.text else None

    tipo_num = norma.find(".//TIPO_NUMERO")
    numero   = tipo_num.findtext("NUMERO") if tipo_num is not None else None
    tipo     = tipo_num.findtext("DESCRIPCION") if tipo_num is not None else None

    titulo = campo("TITULO")
    if titulo:
        titulo = titulo.title()

    texto      = campo("TEXTO")
    organismos = [o.text.strip() for o in norma.findall(".//ORGANISMO") if o.text]

    return {
        "id_norma":           norma.get("idNorma"),
        "numero":             numero,
        "tipo":               tipo,
        "titulo":             titulo,
        "fecha_publicacion":  campo("FECHA_PUBLICACION"),
        "fecha_promulgacion": campo("FECHA_PROMULGACION"),
        "organismos":         organismos,
        "texto":              texto[:3000] if texto else None,
        "url": f"https://www.leychile.cl/Navegar?idNorma={norma.get('idNorma')}" if norma.get("idNorma") else None,
    }


@router.get("/recientes")
def leyes_recientes(cantidad: int = Query(default=50, le=50)):
    url = URL_BASE.format(cantidad=cantidad)
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al consultar leychile.cl: {e}")

    parser = etree.XMLParser(recover=True)
    try:
        root = etree.fromstring(r.content, parser=parser)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al parsear XML: {e}")

    leyes = [_parsear_norma(norma) for norma in root.iter("NORMA")]
    return {"total": len(leyes), "fuente": "Biblioteca del Congreso Nacional de Chile", "leyes": leyes}


class ResumenRequest(BaseModel):
    titulo: str
    numero: str | None = None
    texto:  str


@router.post("/{id_norma}/resumen")
def resumen_ley(id_norma: str, body: ResumenRequest, db: Session = Depends(get_db)):
    import anthropic

    cache_key = f"LEY-{id_norma}"
    cached = db.query(ResumenIA).filter(ResumenIA.boletin == cache_key).first()
    if cached:
        return {"id_norma": id_norma, "resumen": cached.resumen, "cached": True}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key no configurada")

    try:
        client  = anthropic.Anthropic(api_key=api_key)
        mensaje = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 400,
            messages   = [{
                "role":    "user",
                "content": (
                    f"Explica esta ley chilena en texto plano simple, sin markdown, sin simbolos #, *, ni negritas.\n\n"
                    f"Ley N° {body.numero or id_norma}: {body.titulo}\n\n"
                    f"Texto:\n{body.texto[:1500]}\n\n"
                    f"Escribe exactamente 3 parrafos cortos: que hace la ley, a quien afecta, y su impacto cotidiano. "
                    f"Solo texto plano sin ningun formato especial."
                )
            }]
        )
        resumen = mensaje.content[0].text

        # Limpiar cualquier markdown que haya podido colar
        import re
        resumen = re.sub(r'#+\s*', '', resumen)
        resumen = re.sub(r'\*+', '', resumen)
        resumen = resumen.strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar resumen: {e}")

    try:
        db.add(ResumenIA(
            boletin          = cache_key,
            titulo           = (body.titulo or "")[:200],
            resumen          = resumen,
            fecha_generacion = datetime.now(timezone.utc).replace(tzinfo=None),
        ))
        db.commit()
    except Exception:
        db.rollback()
        # Si falla el caché igual retornamos el resumen
        pass

    return {"id_norma": id_norma, "resumen": resumen, "cached": False}
