"""Modelos SQLAlchemy para todas las tablas del sistema SIF-Bancario."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime,
    Text, BigInteger, Index
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Captacion(Base):
    __tablename__ = "captaciones"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    fecha            = Column(Date, nullable=False, index=True)
    entidad          = Column(String(100))
    tipo_entidad     = Column(String(10))
    localidad        = Column(String(100))
    moneda           = Column(String(10))
    sector           = Column(String(100))
    tipo_depositante = Column(String(100))
    monto            = Column(Float)
    numero_cuentas   = Column(Integer)
    fuente_endpoint  = Column(String(80))
    cargado_en       = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_cap_fecha_entidad", "fecha", "entidad"),
    )


class CarteraCredito(Base):
    __tablename__ = "cartera_creditos"
    id                   = Column(Integer, primary_key=True, autoincrement=True)
    fecha                = Column(Date, nullable=False, index=True)
    entidad              = Column(String(100))
    tipo_entidad         = Column(String(10))
    clasificacion_riesgo = Column(String(50))
    genero               = Column(String(20))
    localidad            = Column(String(100))
    moneda               = Column(String(10))
    sector_economico     = Column(String(100))
    tipo_cartera         = Column(String(80))
    saldo                = Column(Float)
    numero_deudores      = Column(Integer)
    fuente_endpoint      = Column(String(80))
    cargado_en           = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_cart_fecha_entidad", "fecha", "entidad"),
    )


class EstadoFinanciero(Base):
    __tablename__ = "estados_financieros"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    fecha        = Column(Date, nullable=False, index=True)
    entidad      = Column(String(100))
    tipo_entidad = Column(String(10))
    cuenta       = Column(String(20))
    descripcion  = Column(String(200))
    monto        = Column(Float)
    tipo_estado  = Column(String(20))   # EIF o EIC
    cargado_en   = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_ef_fecha_entidad", "fecha", "entidad"),
    )


class Indicador(Base):
    __tablename__ = "indicadores"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    fecha           = Column(Date, nullable=False, index=True)
    entidad         = Column(String(100))
    tipo_entidad    = Column(String(10))
    tipo_indicador  = Column(String(80))
    nombre          = Column(String(200))
    valor           = Column(Float)
    fuente_endpoint = Column(String(80))
    cargado_en      = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_ind_fecha_tipo", "fecha", "tipo_indicador"),
    )


class Solvencia(Base):
    __tablename__ = "solvencia"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    fecha        = Column(Date, nullable=False, index=True)
    entidad      = Column(String(100))
    tipo_entidad = Column(String(10))
    componente   = Column(String(100))
    valor        = Column(Float)
    cargado_en   = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_sol_fecha_entidad", "fecha", "entidad"),
    )


class LogCarga(Base):
    __tablename__ = "log_cargas"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    endpoint   = Column(String(100))
    registros  = Column(Integer)
    estado     = Column(String(20))   # OK / ERROR
    mensaje    = Column(Text)
    inicio     = Column(DateTime)
    fin        = Column(DateTime)


class MacroTasas(Base):
    __tablename__ = "macro_tasas"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    fecha        = Column(Date, nullable=False, unique=True, index=True)
    tpm          = Column(Float)   # con ruido
    tpm_nominal  = Column(Float)   # valor oficial


class MacroInflacion(Base):
    __tablename__ = "macro_inflacion"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    fecha               = Column(Date, nullable=False, unique=True, index=True)
    ipc_nivel           = Column(Float)
    ipc_mensual_pct     = Column(Float)
    ipc_interanual_pct  = Column(Float)


class MacroTipoCambio(Base):
    __tablename__ = "macro_tipo_cambio"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    fecha           = Column(Date, nullable=False, unique=True, index=True)
    venta_dop_usd   = Column(Float)
    compra_dop_usd  = Column(Float)
    spread          = Column(Float)


class MacroPIB(Base):
    __tablename__ = "macro_pib"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    fecha               = Column(Date, nullable=False, unique=True, index=True)
    trimestre           = Column(String(10))
    crecimiento_pct     = Column(Float)
    pib_millones_dop    = Column(Float)


class MacroRemesas(Base):
    __tablename__ = "macro_remesas"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    fecha               = Column(Date, nullable=False, unique=True, index=True)
    monto_usd_millones  = Column(Float)
    monto_anualizado    = Column(Float)


def create_all_tables(engine):
    Base.metadata.create_all(bind=engine)
