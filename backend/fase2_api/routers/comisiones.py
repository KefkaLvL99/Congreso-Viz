# ============================================================
# routers/comisiones.py
# ============================================================
# Define los endpoints relacionados a comisiones del Senado:
#
#   GET /comisiones             → lista todas las comisiones vigentes
#   GET /comisiones/{id}        → detalle de una comisión con sus integrantes
#
# Los datos vienen de:
#   https://tramitacion.senado.cl/wspublico/comisiones.php
# ============================================================

import requests
from lxml import etree
from fastapi import APIRouter, HTTPException

# ── CONFIGURACIÓN ────────────────────────────────────────────

router = APIRouter()

URL_COMISIONES = "https://tramitacion.senado.cl/wspublico/comisiones.php"

TIMEOUT = 15


# ── FUNCIÓN AUXILIAR ─────────────────────────────────────────

def obtener_comisiones_desde_api():
    """
    Consulta la API del Senado, parsea el XML y retorna
    una lista de comisiones, cada una con sus integrantes.
    """

    # 1. Consultar la API
    try:
        respuesta = requests.get(URL_COMISIONES, timeout=TIMEOUT)
        respuesta.raise_for_status()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="La API del Senado no respondió a tiempo")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error al consultar la API del Senado: {e}")

    # 2. Parsear XML
    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(respuesta.content, parser=parser)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al parsear XML: {e}")

    # 3. Convertir cada nodo <comision> en un diccionario
    comisiones = []

    for nodo in root.iter("comision"):

        # Helper para leer un campo simple del nodo comision
        def campo(tag):
            elemento = nodo.find(tag)
            if elemento is not None and elemento.text:
                return elemento.text.strip()
            return None

        # 3a. Parsear los integrantes (nodo anidado)
        integrantes = []
        nodo_integrantes = nodo.find("integrantes")

        if nodo_integrantes is not None:
            for integrante in nodo_integrantes.iter("integrante"):

                # Helper para leer campos del integrante
                def campo_i(tag):
                    elemento = integrante.find(tag)
                    if elemento is not None and elemento.text:
                        return elemento.text.strip()
                    return None

                # Construir nombre completo del integrante
                partes = [
                    campo_i("NOMBRE"),
                    campo_i("APELLIDO_PATERNO"),
                    campo_i("APELLIDO_MATERNO"),
                ]
                nombre_completo = " ".join(p for p in partes if p)

                integrantes.append({
                    "id":             campo_i("PARLID"),
                    "nombre_completo": nombre_completo,
                    "nombre":         campo_i("NOMBRE"),
                    "apellido_paterno": campo_i("APELLIDO_PATERNO"),
                    "apellido_materno": campo_i("APELLIDO_MATERNO"),
                    "email":          campo_i("PARLEMAIL"),
                    "cargo":          campo_i("CARGO"),       # Senador / Senadora
                    "funcion":        campo_i("FUNCION"),     # presidente / None
                    "saludo":         campo_i("SALUDO"),      # Sr. / Sra.
                })

        comisiones.append({
            "id":           campo("id"),
            "nombre":       campo("nombre"),
            "tipo":         campo("tipo"),         # Permanente / Especial / Presupuesto
            "email":        campo("email"),
            "total_integrantes": len(integrantes),
            "integrantes":  integrantes,
        })

    return comisiones


# ── ENDPOINTS ────────────────────────────────────────────────

@router.get("/")
def listar_comisiones():
    """
    Retorna la lista de todas las comisiones vigentes del Senado.
    Incluye nombre, tipo y cantidad de integrantes.

    Ejemplo:
        GET http://localhost:8000/comisiones/
    """
    comisiones = obtener_comisiones_desde_api()

    # Para el listado general no incluimos integrantes completos
    # solo el resumen — el detalle se obtiene por /comisiones/{id}
    resumen = [
        {
            "id":                c["id"],
            "nombre":            c["nombre"],
            "tipo":              c["tipo"],
            "email":             c["email"],
            "total_integrantes": c["total_integrantes"],
        }
        for c in comisiones
    ]

    return {
        "total": len(resumen),
        "fuente": "Senado de Chile - Datos Abiertos",
        "url_fuente": URL_COMISIONES,
        "comisiones": resumen,
    }


@router.get("/{comision_id}")
def obtener_comision(comision_id: str):
    """
    Retorna el detalle completo de una comisión, incluyendo
    todos sus integrantes y sus roles (presidente, etc).

    Ejemplo:
        GET http://localhost:8000/comisiones/185
    """
    comisiones = obtener_comisiones_desde_api()

    resultado = next(
        (c for c in comisiones if c["id"] == comision_id),
        None
    )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró comisión con ID {comision_id}"
        )

    return resultado
