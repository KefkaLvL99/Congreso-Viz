# ============================================================
# models.py
# ============================================================

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Senador(Base):
    __tablename__ = "senadores"

    id                   = Column(String, primary_key=True)
    apellido_paterno     = Column(String)
    apellido_materno     = Column(String)
    nombre               = Column(String)
    nombre_completo      = Column(String)
    region               = Column(String)
    circunscripcion      = Column(String)
    partido              = Column(String)
    telefono             = Column(String, nullable=True)
    email                = Column(String, nullable=True)
    curriculum_url       = Column(String, nullable=True)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    comisiones = relationship("ComisionMiembro", back_populates="senador")
    gastos     = relationship("GastoSenador", back_populates="senador")


class Comision(Base):
    __tablename__ = "comisiones"

    id                   = Column(String, primary_key=True)
    nombre               = Column(String)
    tipo                 = Column(String)
    email                = Column(String, nullable=True)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    miembros = relationship("ComisionMiembro", back_populates="comision")


class ComisionMiembro(Base):
    __tablename__ = "comision_miembros"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    senador_id  = Column(String, ForeignKey("senadores.id"))
    comision_id = Column(String, ForeignKey("comisiones.id"))
    cargo       = Column(String, nullable=True)
    funcion     = Column(String, nullable=True)
    saludo      = Column(String, nullable=True)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    senador  = relationship("Senador",  back_populates="comisiones")
    comision = relationship("Comision", back_populates="miembros")


class Diputado(Base):
    __tablename__ = "diputados"

    id               = Column(String, primary_key=True)
    nombre_completo  = Column(String)
    nombre           = Column(String)
    apellido_paterno = Column(String)
    region           = Column(String, nullable=True)
    distrito         = Column(String, nullable=True)
    periodo          = Column(String, nullable=True)
    partido          = Column(String, nullable=True)
    bancada          = Column(String, nullable=True)
    email            = Column(String, nullable=True)
    url_perfil       = Column(String, nullable=True)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow)


class Votacion(Base):
    __tablename__ = "votaciones"

    id              = Column(String, primary_key=True)
    boletin         = Column(String)
    titulo          = Column(Text)
    camara          = Column(String)
    etapa           = Column(String)
    estado          = Column(String)
    sesion          = Column(String)
    fecha           = Column(String)
    tema            = Column(Text)
    tipo_votacion   = Column(String)
    votos_si        = Column(Integer, default=0)
    votos_no        = Column(Integer, default=0)
    abstenciones    = Column(Integer, default=0)
    pareos          = Column(Integer, default=0)
    quorum          = Column(String, nullable=True)
    resultado       = Column(String)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    detalles = relationship("VotoDetalle", back_populates="votacion",
                            cascade="all, delete-orphan")


class VotoDetalle(Base):
    __tablename__ = "voto_detalles"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    votacion_id   = Column(String, ForeignKey("votaciones.id", ondelete="CASCADE"))
    parlamentario = Column(String)
    seleccion     = Column(String)

    votacion = relationship("Votacion", back_populates="detalles")


class ResumenIA(Base):
    __tablename__ = "resumenes_ia"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    boletin          = Column(String, unique=True, index=True)
    titulo           = Column(Text)
    resumen          = Column(Text)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)


class GastoSenador(Base):
    """
    Gastos operacionales de senadores vigentes.
    Fuente: web-back.senado.cl/api/transparency/expenses/senator-Operational-expenses
    Categorías: OFICINAS, TELEFONÍA, TRASLACIÓN, DIFUSIÓN, etc.
    """
    __tablename__ = "gastos_senadores"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    senador_id   = Column(String, ForeignKey("senadores.id"), nullable=True)
    ano          = Column(Integer)
    mes          = Column(Integer)
    categoria    = Column(String)   # OFICINAS PARLAMENTARIAS, TELEFONÍA, etc.
    monto        = Column(BigInteger)  # en pesos chilenos
    # Nombre tal como viene de la API (para casos sin match)
    appaterno    = Column(String)
    apmaterno    = Column(String)
    nombre_api   = Column(String)

    senador = relationship("Senador", back_populates="gastos")
