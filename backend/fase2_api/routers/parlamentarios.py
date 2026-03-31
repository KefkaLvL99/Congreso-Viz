# ============================================================
# routers/parlamentarios.py
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import VotoDetalle, Votacion, Senador, Diputado

router = APIRouter()


def _parsear_nombre_xml(nombre: str) -> dict:
    resultado = {"apellido_paterno": "", "inicial_materno": "", "nombre": ""}
    if "," not in nombre:
        resultado["apellido_paterno"] = nombre.strip()
        return resultado
    partes         = nombre.split(",", 1)
    apellido_parte = partes[0].strip()
    resultado["nombre"] = partes[1].strip()
    palabras = apellido_parte.split()
    if len(palabras) >= 2:
        resultado["inicial_materno"]  = palabras[-1].replace(".", "").upper()
        resultado["apellido_paterno"] = " ".join(palabras[:-1])
    else:
        resultado["apellido_paterno"] = apellido_parte
    return resultado


def _buscar_votos(nombre: str, db: Session):
    """
    Busca votos soportando múltiples formatos:
    - "Achurra Díaz, Ignacio"   (VotoDetalle Cámara WS)
    - "Flores O., Camila"       (VotoDetalle Senado XML)
    - "Ignacio Achurra Díaz"    (nombre_completo BD con apellido materno)
    - "Ignacio Achurra"         (nombre_completo BD sin apellido materno)
    """
    # Intento 1: búsqueda directa
    todos = db.query(VotoDetalle).filter(
        VotoDetalle.parlamentario.ilike(f"%{nombre}%")
    ).all()
    if todos:
        return todos

    partes = nombre.strip().split()

    # Intento 2: "Nombre Apellido1 Apellido2" → buscar Apellido1 + Nombre
    if len(partes) >= 3:
        apellido = partes[1]
        nom_pila = partes[0]
        todos = db.query(VotoDetalle).filter(
            VotoDetalle.parlamentario.ilike(f"%{apellido}%"),
            VotoDetalle.parlamentario.ilike(f"%{nom_pila}%"),
        ).all()
        if todos:
            return todos

    # Intento 3: "Nombre Apellido" (2 palabras)
    if len(partes) == 2:
        apellido = partes[1]
        nom_pila = partes[0]
        todos = db.query(VotoDetalle).filter(
            VotoDetalle.parlamentario.ilike(f"%{apellido}%"),
            VotoDetalle.parlamentario.ilike(f"%{nom_pila}%"),
        ).all()
        if todos:
            return todos

    return []


def _buscar_votos_paginados(nombre: str, db: Session, limite: int, offset: int):
    """Igual que _buscar_votos pero paginado."""
    # Intento 1: búsqueda directa
    q = db.query(VotoDetalle).filter(
        VotoDetalle.parlamentario.ilike(f"%{nombre}%")
    )
    if q.count() > 0:
        return q.offset(offset).limit(limite).all()

    partes = nombre.strip().split()

    # Intento 2: apellido + nombre de pila (3+ palabras)
    if len(partes) >= 3:
        apellido = partes[1]
        nom_pila = partes[0]
        q2 = db.query(VotoDetalle).filter(
            VotoDetalle.parlamentario.ilike(f"%{apellido}%"),
            VotoDetalle.parlamentario.ilike(f"%{nom_pila}%"),
        )
        if q2.count() > 0:
            return q2.offset(offset).limit(limite).all()

    # Intento 3: 2 palabras
    if len(partes) == 2:
        apellido = partes[1]
        nom_pila = partes[0]
        q3 = db.query(VotoDetalle).filter(
            VotoDetalle.parlamentario.ilike(f"%{apellido}%"),
            VotoDetalle.parlamentario.ilike(f"%{nom_pila}%"),
        )
        if q3.count() > 0:
            return q3.offset(offset).limit(limite).all()

    return []


def _buscar_en_senadores(apellido, inicial_m, nombre_prl, db):
    if inicial_m and nombre_prl:
        sen = db.query(Senador).filter(
            Senador.apellido_paterno.ilike(f"{apellido}%"),
            Senador.apellido_materno.ilike(f"{inicial_m}%"),
            Senador.nombre.ilike(f"{nombre_prl}%"),
        ).first()
        if sen:
            return sen
    if nombre_prl:
        sen = db.query(Senador).filter(
            Senador.apellido_paterno.ilike(f"{apellido}%"),
            Senador.nombre.ilike(f"{nombre_prl}%"),
        ).first()
        if sen:
            return sen
    lista = db.query(Senador).filter(
        Senador.apellido_paterno.ilike(f"{apellido}%")
    ).all()
    if len(lista) == 1:
        return lista[0]
    return None


def _buscar_en_diputados(apellido, inicial_m, nombre_prl, db):
    if nombre_prl:
        candidatos = db.query(Diputado).filter(
            Diputado.apellido_paterno.ilike(f"{apellido}%"),
            Diputado.nombre_completo.ilike(f"%{nombre_prl}%"),
        ).all()
        if len(candidatos) == 1:
            return candidatos[0]
        if len(candidatos) > 1 and inicial_m:
            for d in candidatos:
                if d.nombre_completo and d.nombre and d.apellido_paterno:
                    resto = (d.nombre_completo
                             .replace(d.nombre, "", 1)
                             .replace(d.apellido_paterno, "", 1)
                             .strip())
                    if resto and resto[0].upper() == inicial_m.upper():
                        return d
            return candidatos[0]
    lista = db.query(Diputado).filter(
        Diputado.apellido_paterno.ilike(f"{apellido}%")
    ).all()
    if len(lista) == 1:
        return lista[0]
    return None


def _buscar_info_parlamentario(nombre: str, db: Session) -> dict:
    info = {
        "partido": None, "bancada": None, "region": None,
        "camara": None, "circunscripcion": None, "distrito": None,
        "cargo_actual": None,
    }

    if "," in nombre:
        p = _parsear_nombre_xml(nombre)
    else:
        partes = nombre.strip().split()
        p = {
            "apellido_paterno": partes[1] if len(partes) >= 2 else (partes[0] if partes else ""),
            "inicial_materno":  "",
            "nombre":           partes[0] if partes else "",
        }

    apellido  = p["apellido_paterno"]
    inicial_m = p["inicial_materno"]
    nombre_p  = p["nombre"]

    if not apellido or len(apellido) < 2:
        return info

    sen = _buscar_en_senadores(apellido, inicial_m, nombre_p, db)
    if sen:
        info.update({
            "partido":         sen.partido,
            "region":          sen.region,
            "circunscripcion": sen.circunscripcion,
            "camara":          "Senado",
            "cargo_actual":    "Senadora/or",
        })
        return info

    dip = _buscar_en_diputados(apellido, inicial_m, nombre_p, db)
    if dip:
        info.update({
            "partido":      dip.partido,
            "bancada":      dip.bancada,
            "region":       dip.region,
            "distrito":     dip.distrito,
            "camara":       "Cámara de Diputados",
            "cargo_actual": "Diputada/o",
        })
        return info

    return info


@router.get("/")
def listar_parlamentarios(
    db:     Session = Depends(get_db),
    buscar: str     = Query(default=None),
):
    query = (
        db.query(
            VotoDetalle.parlamentario,
            func.count(VotoDetalle.id).label("total_votos")
        )
        .group_by(VotoDetalle.parlamentario)
        .order_by(VotoDetalle.parlamentario)
    )
    if buscar:
        query = query.filter(VotoDetalle.parlamentario.ilike(f"%{buscar}%"))
    resultados = query.all()
    return {
        "total": len(resultados),
        "parlamentarios": [
            {"nombre": r.parlamentario, "total_votos": r.total_votos}
            for r in resultados
        ]
    }


@router.get("/{nombre}/votos")
def votos_parlamentario(
    nombre:  str,
    db:      Session = Depends(get_db),
    limite:  int     = Query(default=20, le=100),
    offset:  int     = Query(default=0),
):
    todos = _buscar_votos(nombre, db)

    if not todos:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron votos para '{nombre}'"
        )

    total  = len(todos)
    conteo = {"Si": 0, "No": 0, "Abstencion": 0, "Pareo": 0}
    for d in todos:
        if d.seleccion in conteo:
            conteo[d.seleccion] += 1

    nombre_real = todos[0].parlamentario
    info        = _buscar_info_parlamentario(nombre_real, db)

    detalles_paginados = _buscar_votos_paginados(nombre, db, limite, offset)

    historial = []
    for d in detalles_paginados:
        v = db.query(Votacion).filter(Votacion.id == d.votacion_id).first()
        if v:
            historial.append({
                "votacion_id":   v.id,
                "boletin":       v.boletin,
                "titulo":        v.titulo,
                "fecha":         v.fecha,
                "camara":        v.camara,
                "resultado":     v.resultado,
                "seleccion":     d.seleccion,
                "tipo_votacion": v.tipo_votacion,
            })

    return {
        "parlamentario":   nombre_real,
        "partido":         info["partido"],
        "bancada":         info["bancada"],
        "region":          info["region"],
        "circunscripcion": info["circunscripcion"],
        "distrito":        info["distrito"],
        "camara":          info["camara"],
        "cargo_actual":    info["cargo_actual"],
        "total_votos":     total,
        "estadisticas": {
            "si":         conteo["Si"],
            "no":         conteo["No"],
            "abstencion": conteo["Abstencion"],
            "pareo":      conteo["Pareo"],
        },
        "limite":    limite,
        "offset":    offset,
        "historial": historial,
    }
