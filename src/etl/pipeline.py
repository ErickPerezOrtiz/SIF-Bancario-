"""Pipeline ETL completo: API SB → MySQL."""
import logging
from datetime import datetime, date
from typing import Optional
import pandas as pd
from sqlalchemy import text

from src.api.client import SBApiClient
from src.db.connection import get_engine
from src.db.models import (
    Captacion, CarteraCredito, EstadoFinanciero,
    Indicador, Solvencia, LogCarga, create_all_tables
)

logger = logging.getLogger(__name__)


def _safe_float(val):
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _parse_date(val) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%m/%Y", "%Y-%m"):
        try:
            return datetime.strptime(str(val)[:10], fmt).date()
        except ValueError:
            continue
    return None


class ETLPipeline:
    def __init__(self):
        self.client = SBApiClient()
        self.engine = get_engine()
        create_all_tables(self.engine)

    def _log_carga(self, endpoint: str, registros: int, estado: str,
                   mensaje: str, inicio: datetime, fin: datetime):
        with self.engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO log_cargas
                        (endpoint, registros, estado, mensaje, inicio, fin)
                        VALUES (:ep, :reg, :est, :msg, :ini, :fin)"""),
                {"ep": endpoint, "reg": registros, "est": estado,
                 "msg": mensaje, "ini": inicio, "fin": fin}
            )

    def _bulk_insert(self, records: list, table_cls):
        if not records:
            return 0
        with self.engine.begin() as conn:
            conn.execute(table_cls.__table__.insert(), records)
        return len(records)

    # ── CAPTACIONES ──────────────────────────────────────────────────────────

    def cargar_captaciones(self):
        sub_endpoints = {
            "captaciones_localidad":        self.client.captaciones_localidad,
            "captaciones_moneda":           self.client.captaciones_moneda,
            "captaciones_sector":           self.client.captaciones_sector,
            "captaciones_tipo_depositante": self.client.captaciones_tipo_depositante,
        }
        total = 0
        for nombre, metodo in sub_endpoints.items():
            inicio = datetime.utcnow()
            try:
                raw = metodo()
                records = []
                for r in raw:
                    records.append({
                        "fecha":            _parse_date(r.get("fecha") or r.get("anio")),
                        "entidad":          str(r.get("entidad", r.get("institucion", ""))),
                        "tipo_entidad":     str(r.get("tipoEntidad", r.get("tipo_entidad", ""))),
                        "localidad":        str(r.get("localidad", r.get("provincia", ""))),
                        "moneda":           str(r.get("moneda", "")),
                        "sector":           str(r.get("sector", "")),
                        "tipo_depositante": str(r.get("tipoDepositante", r.get("tipo_depositante", ""))),
                        "monto":            _safe_float(r.get("monto", r.get("saldo", r.get("captaciones")))),
                        "numero_cuentas":   _safe_int(r.get("numeroCuentas", r.get("numero_cuentas"))),
                        "fuente_endpoint":  nombre,
                    })
                n = self._bulk_insert(records, Captacion)
                total += n
                self._log_carga(nombre, n, "OK", "", inicio, datetime.utcnow())
                logger.info("Captaciones [%s]: %d filas insertadas", nombre, n)
            except Exception as e:
                self._log_carga(nombre, 0, "ERROR", str(e), inicio, datetime.utcnow())
                logger.error("Error en %s: %s", nombre, e)
        return total

    # ── CARTERA DE CRÉDITOS ───────────────────────────────────────────────────

    def cargar_cartera(self):
        sub_endpoints = {
            "cartera_clasificacion_riesgo": self.client.cartera_clasificacion_riesgo,
            "cartera_genero":               self.client.cartera_genero,
            "cartera_localidad":            self.client.cartera_localidad,
            "cartera_moneda":               self.client.cartera_moneda,
            "cartera_sector_economico":     self.client.cartera_sector_economico,
            "cartera_tipo":                 self.client.cartera_tipo,
        }
        total = 0
        for nombre, metodo in sub_endpoints.items():
            inicio = datetime.utcnow()
            try:
                raw = metodo()
                records = []
                for r in raw:
                    records.append({
                        "fecha":                _parse_date(r.get("fecha")),
                        "entidad":              str(r.get("entidad", r.get("institucion", ""))),
                        "tipo_entidad":         str(r.get("tipoEntidad", "")),
                        "clasificacion_riesgo": str(r.get("clasificacionRiesgo", r.get("clasificacion", ""))),
                        "genero":               str(r.get("genero", r.get("sexo", ""))),
                        "localidad":            str(r.get("localidad", r.get("provincia", ""))),
                        "moneda":               str(r.get("moneda", "")),
                        "sector_economico":     str(r.get("sectorEconomico", r.get("sector", ""))),
                        "tipo_cartera":         str(r.get("tipoCartera", r.get("tipo", ""))),
                        "saldo":                _safe_float(r.get("saldo", r.get("monto"))),
                        "numero_deudores":      _safe_int(r.get("numeroDeudores", r.get("deudores"))),
                        "fuente_endpoint":      nombre,
                    })
                n = self._bulk_insert(records, CarteraCredito)
                total += n
                self._log_carga(nombre, n, "OK", "", inicio, datetime.utcnow())
                logger.info("Cartera [%s]: %d filas insertadas", nombre, n)
            except Exception as e:
                self._log_carga(nombre, 0, "ERROR", str(e), inicio, datetime.utcnow())
                logger.error("Error en %s: %s", nombre, e)
        return total

    # ── ESTADOS FINANCIEROS ──────────────────────────────────────────────────

    def cargar_estados_financieros(self):
        sub_endpoints = {
            "estados_financieros_eif": (self.client.estados_financieros_eif, "EIF"),
            "estados_financieros_eic": (self.client.estados_financieros_eic, "EIC"),
        }
        total = 0
        for nombre, (metodo, tipo) in sub_endpoints.items():
            inicio = datetime.utcnow()
            try:
                raw = metodo()
                records = []
                for r in raw:
                    records.append({
                        "fecha":        _parse_date(r.get("fecha")),
                        "entidad":      str(r.get("entidad", r.get("institucion", ""))),
                        "tipo_entidad": str(r.get("tipoEntidad", "")),
                        "cuenta":       str(r.get("cuenta", r.get("codigoCuenta", ""))),
                        "descripcion":  str(r.get("descripcion", r.get("nombreCuenta", ""))),
                        "monto":        _safe_float(r.get("monto", r.get("saldo", r.get("valor")))),
                        "tipo_estado":  tipo,
                    })
                n = self._bulk_insert(records, EstadoFinanciero)
                total += n
                self._log_carga(nombre, n, "OK", "", inicio, datetime.utcnow())
                logger.info("Estados Financieros [%s]: %d filas insertadas", nombre, n)
            except Exception as e:
                self._log_carga(nombre, 0, "ERROR", str(e), inicio, datetime.utcnow())
                logger.error("Error en %s: %s", nombre, e)
        return total

    # ── INDICADORES ──────────────────────────────────────────────────────────

    def cargar_indicadores(self):
        sub_endpoints = {
            "indicadores_sistema":     (self.client.indicadores_sistema,    "sistema"),
            "indicadores_financieros": (self.client.indicadores_financieros, "financiero"),
            "indicadores_morosidad":   (self.client.indicadores_morosidad,  "morosidad"),
        }
        total = 0
        for nombre, (metodo, tipo) in sub_endpoints.items():
            inicio = datetime.utcnow()
            try:
                raw = metodo()
                records = []
                for r in raw:
                    records.append({
                        "fecha":            _parse_date(r.get("fecha")),
                        "entidad":          str(r.get("entidad", r.get("institucion", ""))),
                        "tipo_entidad":     str(r.get("tipoEntidad", "")),
                        "tipo_indicador":   tipo,
                        "nombre":           str(r.get("nombre", r.get("indicador", ""))),
                        "valor":            _safe_float(r.get("valor")),
                        "fuente_endpoint":  nombre,
                    })
                n = self._bulk_insert(records, Indicador)
                total += n
                self._log_carga(nombre, n, "OK", "", inicio, datetime.utcnow())
                logger.info("Indicadores [%s]: %d filas insertadas", nombre, n)
            except Exception as e:
                self._log_carga(nombre, 0, "ERROR", str(e), inicio, datetime.utcnow())
                logger.error("Error en %s: %s", nombre, e)
        return total

    # ── SOLVENCIA ────────────────────────────────────────────────────────────

    def cargar_solvencia(self):
        sub_endpoints = {
            "solvencia":            self.client.solvencia,
            "solvencia_componentes": self.client.solvencia_componentes,
        }
        total = 0
        for nombre, metodo in sub_endpoints.items():
            inicio = datetime.utcnow()
            try:
                raw = metodo()
                records = []
                for r in raw:
                    records.append({
                        "fecha":        _parse_date(r.get("fecha")),
                        "entidad":      str(r.get("entidad", r.get("institucion", ""))),
                        "tipo_entidad": str(r.get("tipoEntidad", "")),
                        "componente":   str(r.get("componente", r.get("nombre", nombre))),
                        "valor":        _safe_float(r.get("valor", r.get("indice"))),
                    })
                n = self._bulk_insert(records, Solvencia)
                total += n
                self._log_carga(nombre, n, "OK", "", inicio, datetime.utcnow())
                logger.info("Solvencia [%s]: %d filas insertadas", nombre, n)
            except Exception as e:
                self._log_carga(nombre, 0, "ERROR", str(e), inicio, datetime.utcnow())
                logger.error("Error en %s: %s", nombre, e)
        return total

    # ── PIPELINE COMPLETO ─────────────────────────────────────────────────────

    def run_all(self) -> dict:
        logger.info("=" * 60)
        logger.info("  INICIANDO PIPELINE ETL — SIF-BANCARIO")
        logger.info("=" * 60)
        resultados = {}
        pasos = [
            ("captaciones",          self.cargar_captaciones),
            ("cartera_creditos",     self.cargar_cartera),
            ("estados_financieros",  self.cargar_estados_financieros),
            ("indicadores",          self.cargar_indicadores),
            ("solvencia",            self.cargar_solvencia),
        ]
        for nombre, func in pasos:
            logger.info("▶ Cargando: %s", nombre)
            resultados[nombre] = func()

        total = sum(resultados.values())
        logger.info("=" * 60)
        logger.info("  PIPELINE COMPLETO — %d registros totales", total)
        logger.info("  Detalle: %s", resultados)
        logger.info("=" * 60)
        return resultados
