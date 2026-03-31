# ============================================================
# database.py - Configuración de la base de datos
# ============================================================
# Este archivo hace UNA sola cosa: crear la conexión a SQLite
# y dejarla lista para que el resto del proyecto la use.
#
# SQLite guarda todo en un archivo local llamado congreso.db
# que se crea automáticamente la primera vez que corres el servidor.
# Puedes ver ese archivo en la carpeta fase2_api/ — es toda tu BD.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── CONFIGURACIÓN DE LA BASE DE DATOS ───────────────────────

# La URL le dice a SQLAlchemy qué motor usar y dónde está el archivo.
# "sqlite:///" significa SQLite local.
# "./congreso.db" es la ruta del archivo — se crea en la misma carpeta.
DATABASE_URL = "sqlite:///./congreso.db"

# El engine es el motor de la base de datos.
# connect_args={"check_same_thread": False} es necesario para SQLite
# cuando FastAPI maneja múltiples requests al mismo tiempo.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal es una fábrica de sesiones.
# Cada vez que queremos leer o escribir en la BD, creamos una sesión,
# hacemos lo que necesitamos, y la cerramos.
# autocommit=False → los cambios no se guardan solos, hay que confirmarlos
# autoflush=False  → los cambios no se envían solos a la BD
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base es la clase padre de todos los modelos (tablas).
# Cuando defines una tabla en models.py, heredas de esta Base.
Base = declarative_base()


# ── FUNCIÓN UTILITARIA ───────────────────────────────────────

def get_db():
    """
    Generador que crea una sesión de base de datos, la entrega,
    y la cierra automáticamente cuando termina el request.

    Se usa como dependencia en los endpoints de FastAPI:
        def mi_endpoint(db = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db        # entrega la sesión al endpoint
    finally:
        db.close()      # siempre cierra, aunque haya un error
