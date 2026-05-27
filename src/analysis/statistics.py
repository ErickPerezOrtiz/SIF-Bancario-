"""Análisis estadístico descriptivo — API v2 → MySQL → CSV (en ese orden)."""
import logging
import os
import pathlib
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy import text

log = logging.getLogger(__name__)
DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "data" / "processed"


# ── Helpers de módulo ─────────────────────────────────────────────────────────

def _safe_float(val):
    """Conversión segura a float; devuelve None si falla."""
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _parse_period(val) -> str | None:
    """Convierte varios formatos de fecha a 'YYYY-MM'. Devuelve None si no parseable."""
    if val is None:
        return None
    s = str(val).strip()
    # YYYY-MM-DD o YYYY-MM
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    for fmt in ("%d/%m/%Y", "%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y-%m")
        except ValueError:
            continue
    return None


class FinancialAnalyzer:
    # Caché compartido entre instancias — se llena la primera vez que se llama a la API
    _API_CACHE: dict[str, pd.DataFrame] = {}
    # Bandera: True cuando preload_all() terminó (éxito o fallo)
    _PRELOAD_DONE: bool = False

    def __init__(self):
        self._engine = None
        self._csv_cache: dict[str, pd.DataFrame] = {}
        self._v2_client = None   # inicializado lazy en _api_v2()

    @classmethod
    def preload_all(cls):
        """
        Precarga todos los endpoints de la API en _API_CACHE.
        Diseñado para correr en un daemon thread al arrancar el servidor.
        Establece _PRELOAD_DONE=True al terminar (éxito o fallo).
        """
        import time
        az = cls()
        t0 = time.time()
        print("PRELOAD: iniciando precarga de caché en background…")

        steps = [
            ("captaciones/localidad", az._fetch_captaciones_localidad_api),
            ("indicadores (financieros+principales+morosidad)", az._fetch_indicadores_api),
            ("solvencia/componentes", az._fetch_solvencia_api),
            ("cartera/moneda (total KPI)", az._fetch_cartera_total_api),
        ]
        for nombre, fn in steps:
            try:
                print(f"PRELOAD: cargando {nombre}…")
                fn()
                print(f"PRELOAD: ✓ {nombre} ({time.time()-t0:.0f}s)")
            except Exception as e:
                print(f"PRELOAD: ✗ {nombre} error: {e}")

        cls._PRELOAD_DONE = True
        print(f"PRELOAD: completado en {time.time()-t0:.0f}s — caché listo")

    # ── Cliente API v2 ────────────────────────────────────────────────────────

    def _api_v2(self):
        """Devuelve SBApiClientV2 (lazy init). Devuelve None si la API no está disponible."""
        if self._v2_client is not None:
            return self._v2_client
        try:
            from src.api.client import SBApiClientV2
            self._v2_client = SBApiClientV2()
            print(f"DEBUG: SBApiClientV2 inicializado — key presente: {bool(os.getenv('SB_API_KEY'))}")
            return self._v2_client
        except Exception as e:
            print(f"DEBUG ERROR: SBApiClientV2 no disponible: {e}")
            log.warning("SBApiClientV2 no disponible: %s", e)
            return None

    def _fetch_indicadores_api(self) -> pd.DataFrame:
        """
        Descarga los 3 endpoints de indicadores desde la API v2 y los normaliza.
        Resultado cacheado en _API_CACHE['indicadores_api'] para el ciclo de vida del proceso.

        Mapeo de endpoints → estructura real v2:
          financieros          → filas per-entidad  [periodo, indicador, valor]
          morosidad-estresada  → filas per-entidad  [periodo, vencido, cobranza, reestructuradoRea, carteraTotal]
          principales          → fila agregada/periodo [periodo, morosidad, roa, margen, ...]
        """
        key = "indicadores_api"
        if key in FinancialAnalyzer._API_CACHE:
            return FinancialAnalyzer._API_CACHE[key].copy()

        # Modo producción: CSV pre-generado por scripts/generar_datos.py
        _csv_cache = DATA_DIR / "cache_indicadores.csv"
        if _csv_cache.exists():
            df = pd.read_csv(_csv_cache)
            FinancialAnalyzer._API_CACHE[key] = df
            log.info("Indicadores: cargados desde CSV estático (%d filas)", len(df))
            return df.copy()

        client = self._api_v2()
        if client is None:
            return pd.DataFrame()

        # Indicadores de /financieros que realmente usamos en el dashboard.
        # El endpoint se consulta con entidad=TODOS — filtrar a BANCOS MÚLTIPLES.
        _FINANCIEROS_KEPT = {
            "Activos Netos Totales / Patrimonio Neto",   # Apalancamiento (escala alta)
            "Margen de Intermediación Neto",              # Escala porcentual
            "Activos Improductivos / Patrimonio Neto",    # Escala porcentual
            "ROE (Rentabilidad del Patrimonio)",           # → chart de Principales
        }
        _ROE = "ROE (Rentabilidad del Patrimonio)"

        rows: list[dict] = []

        # ── 1. /indicadores/financieros — solo agregados BANCOS MÚLTIPLES ────
        try:
            print("DEBUG: llamando indicadores/financieros API…")
            raw_fin = list(client.indicadores_financieros())
            print(f"DEBUG: indicadores/financieros → {len(raw_fin)} registros recibidos")
            if raw_fin:
                print(f"DEBUG: primera fila ejemplo: {raw_fin[0]}")
            for r in raw_fin:
                if r.get("tipoEntidad") != "BANCOS MÚLTIPLES":
                    continue
                periodo = _parse_period(r.get("periodo") or r.get("fecha"))
                if not periodo:
                    continue
                nombre = str(r.get("indicador", r.get("nombre", ""))).strip()
                if nombre not in _FINANCIEROS_KEPT:
                    continue
                valor = _safe_float(r.get("valor"))
                if valor is None:
                    continue
                tipo = "principales" if nombre == _ROE else "financieros"
                rows.append({"periodo": periodo, "tipo_indicador": tipo,
                              "nombre": nombre, "valor": valor})
        except Exception as e:
            import traceback
            print(f"DEBUG ERROR indicadores/financieros: {e}")
            print(traceback.format_exc())
            log.warning("API indicadores/financieros falló: %s", e)

        # ── 2. /indicadores/morosidad-estresada — calcular ratio ─────────────
        try:
            print("DEBUG: llamando indicadores/morosidad-estresada API…")
            raw_mor = list(client.indicadores_morosidad_estresada())
            print(f"DEBUG: morosidad-estresada → {len(raw_mor)} registros recibidos")
            for r in raw_mor:
                periodo = _parse_period(r.get("periodo") or r.get("fecha"))
                if not periodo:
                    continue
                cartera = _safe_float(r.get("carteraTotal"))
                if not cartera or cartera == 0:
                    continue
                vencido  = _safe_float(r.get("vencido"))   or 0
                cobranza = _safe_float(r.get("cobranza"))  or 0
                reest    = _safe_float(r.get("reestructuradoRea")) or 0
                valor    = (vencido + cobranza + reest) / cartera * 100
                rows.append({"periodo": periodo, "tipo_indicador": "morosidad",
                              "nombre": "Morosidad Estresada", "valor": valor})
        except Exception as e:
            import traceback
            print(f"DEBUG ERROR morosidad-estresada: {e}")
            print(traceback.format_exc())
            log.warning("API indicadores/morosidad-estresada falló: %s", e)

        # ── 3. /indicadores/principales — pivotear columnas a filas ──────────
        PRINCIPALES_MAP = {
            "morosidad": ("morosidad",   "Morosidad Simple"),
            "roa":       ("principales", "ROA"),
            "solvencia": ("principales", "Índice Solvencia"),
        }
        try:
            print("DEBUG: llamando indicadores/principales API…")
            raw_pri = list(client.indicadores_principales())
            print(f"DEBUG: indicadores/principales → {len(raw_pri)} registros recibidos")
            if raw_pri:
                print(f"DEBUG: primera fila ejemplo: {raw_pri[0]}")
            for r in raw_pri:
                periodo = _parse_period(r.get("periodo") or r.get("fecha"))
                if not periodo:
                    continue
                for campo, (tipo, nombre) in PRINCIPALES_MAP.items():
                    valor = _safe_float(r.get(campo))
                    if valor is None:
                        continue
                    rows.append({"periodo": periodo, "tipo_indicador": tipo,
                                  "nombre": nombre, "valor": valor})
                ta = _safe_float(r.get("tasaActiva"))
                tp = _safe_float(r.get("tasaPasiva"))
                if ta is not None and tp is not None:
                    rows.append({"periodo": periodo, "tipo_indicador": "financieros",
                                  "nombre": "Spread de Tasas de Interés",
                                  "valor": ta - tp})
        except Exception as e:
            import traceback
            print(f"DEBUG ERROR indicadores/principales: {e}")
            print(traceback.format_exc())
            log.warning("API indicadores/principales falló: %s", e)

        if not rows:
            FinancialAnalyzer._API_CACHE["indicadores_api"] = pd.DataFrame()
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        result = (df.groupby(["periodo", "tipo_indicador", "nombre"])["valor"]
                   .agg(valor_promedio="mean", valor_min="min",
                        valor_max="max", valor_std="std")
                   .reset_index()
                   .sort_values(["periodo", "tipo_indicador"]))
        FinancialAnalyzer._API_CACHE[key] = result
        log.info("API indicadores: %d filas cacheadas (%d tipos)", len(result),
                 result["tipo_indicador"].nunique())
        return result.copy()

    def _fetch_solvencia_api(self) -> pd.DataFrame:
        """
        Descarga solvencia desde la API v2.
        Resultado cacheado en _API_CACHE['solvencia_api'].
        """
        key = "solvencia_api"
        if key in FinancialAnalyzer._API_CACHE:
            return FinancialAnalyzer._API_CACHE[key].copy()

        # Modo producción: CSV pre-generado por scripts/generar_datos.py
        _csv_cache = DATA_DIR / "cache_solvencia.csv"
        if _csv_cache.exists():
            df = pd.read_csv(_csv_cache)
            FinancialAnalyzer._API_CACHE[key] = df
            log.info("Solvencia: cargada desde CSV estático (%d filas)", len(df))
            return df.copy()

        client = self._api_v2()
        if client is None:
            return pd.DataFrame()

        rows: list[dict] = []
        try:
            for r in client.solvencia():
                # entidad=TODOS devuelve todas las categorías; retener solo BM
                if r.get("tipoEntidad") != "BANCOS MÚLTIPLES":
                    continue
                periodo = _parse_period(r.get("fecha") or r.get("periodo"))
                if periodo is None:
                    continue
                componente = str(r.get("componente", r.get("nombre",
                                  r.get("indicador", "")))).strip()
                valor = _safe_float(r.get("valor", r.get("indice")))
                if valor is None or not componente:
                    continue
                rows.append({"periodo": periodo, "componente": componente, "valor": valor})
        except Exception as e:
            log.warning("API solvencia falló — usando fallback: %s", e)

        if not rows:
            FinancialAnalyzer._API_CACHE[key] = pd.DataFrame()
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        result = (df.groupby(["periodo", "componente"])["valor"]
                   .agg(promedio="mean", minimo="min", maximo="max", entidades="count")
                   .reset_index()
                   .sort_values("periodo", ascending=False))
        FinancialAnalyzer._API_CACHE[key] = result
        log.info("API solvencia: %d filas cacheadas", len(result))
        return result.copy()

    def _fetch_captaciones_localidad_api(self) -> pd.DataFrame:
        """
        Descarga captaciones/localidad desde la API v2.
        Resultado cacheado en _API_CACHE['captaciones_localidad_api'].
        """
        key = "captaciones_localidad_api"
        if key in FinancialAnalyzer._API_CACHE:
            return FinancialAnalyzer._API_CACHE[key].copy()

        # Modo producción: CSV pre-generado por scripts/generar_datos.py
        _csv_cache = DATA_DIR / "cache_captaciones_localidad.csv"
        if _csv_cache.exists():
            df = pd.read_csv(_csv_cache)
            FinancialAnalyzer._API_CACHE[key] = df
            log.info("Captaciones localidad: cargadas desde CSV estático (%d filas)", len(df))
            return df.copy()

        client = self._api_v2()
        if client is None:
            return pd.DataFrame()

        rows: list[dict] = []
        entidades_vistas: set = set()
        periodos_vistos: set = set()
        try:
            print("DEBUG: llamando captaciones/localidad API…")
            raw = list(client.captaciones_localidad())
            print(f"DEBUG: captaciones/localidad → {len(raw)} registros recibidos")
            if raw:
                print(f"DEBUG: primera fila ejemplo: {raw[0]}")
            for r in raw:
                localidad = str(r.get("provincia", r.get("region", ""))).strip()
                monto = _safe_float(r.get("balance", r.get("monto", r.get("saldo"))))
                if not localidad or monto is None:
                    continue
                rows.append({"localidad": localidad, "total_captado": monto})
                ent = str(r.get("entidad", r.get("nombreEntidad", ""))).strip()
                if ent:
                    entidades_vistas.add(ent)
                per = _parse_period(r.get("periodo") or r.get("fecha"))
                if per:
                    periodos_vistos.add(per)
        except Exception as e:
            import traceback
            print(f"DEBUG ERROR captaciones/localidad: {e}")
            print(traceback.format_exc())
            log.warning("API captaciones/localidad falló — usando fallback: %s", e)

        # Cachear conteos para resumen_ejecutivo (se sobreescriben si vienen vacíos)
        if entidades_vistas:
            FinancialAnalyzer._API_CACHE["entidades_count"] = len(entidades_vistas)
        if periodos_vistos:
            FinancialAnalyzer._API_CACHE["periodos_count"] = len(periodos_vistos)

        if not rows:
            FinancialAnalyzer._API_CACHE["captaciones_localidad_api"] = pd.DataFrame()
            return pd.DataFrame()

        result = (pd.DataFrame(rows)
                  .groupby("localidad")["total_captado"]
                  .sum().reset_index()
                  .sort_values("total_captado", ascending=False))
        FinancialAnalyzer._API_CACHE[key] = result
        log.info("API captaciones/localidad: %d filas cacheadas", len(result))
        return result.copy()

    def _fetch_cartera_total_api(self) -> float:
        """
        Suma total de cartera de créditos (todas las monedas) desde la API v2.
        Resultado cacheado en _API_CACHE['cartera_total_api'].
        """
        key = "cartera_total_api"
        if key in FinancialAnalyzer._API_CACHE:
            return FinancialAnalyzer._API_CACHE[key]

        # Modo producción: leer desde cache_meta.csv generado por scripts/generar_datos.py
        _meta_csv = DATA_DIR / "cache_meta.csv"
        if _meta_csv.exists():
            meta = pd.read_csv(_meta_csv)
            total = float(meta["cartera_total_dop"].iloc[0])
            FinancialAnalyzer._API_CACHE[key] = total
            if "entidades_count" not in FinancialAnalyzer._API_CACHE:
                FinancialAnalyzer._API_CACHE["entidades_count"] = int(meta["entidades_count"].iloc[0])
            if "periodos_count" not in FinancialAnalyzer._API_CACHE:
                FinancialAnalyzer._API_CACHE["periodos_count"] = int(meta["periodos_count"].iloc[0])
            log.info("Cartera total: cargada desde CSV estático (%.0f)", total)
            return total

        client = self._api_v2()
        if client is None:
            return 0.0

        total = 0.0
        try:
            print("DEBUG: llamando carteras/creditos/moneda API…")
            raw = list(client.cartera_moneda())
            print(f"DEBUG: cartera/moneda → {len(raw)} registros recibidos")
            if raw:
                print(f"DEBUG: primera fila cartera: {raw[0]}")
            for r in raw:
                v = _safe_float(r.get("saldo", r.get("balance", r.get("monto"))))
                if v is not None:
                    total += v
            # Acumular también entidades y períodos si no los tenemos aún
            if "entidades_count" not in FinancialAnalyzer._API_CACHE:
                ents = {str(r.get("entidad", r.get("nombreEntidad", ""))).strip() for r in raw}
                ents.discard("")
                if ents:
                    FinancialAnalyzer._API_CACHE["entidades_count"] = len(ents)
            if "periodos_count" not in FinancialAnalyzer._API_CACHE:
                pers = {_parse_period(r.get("periodo") or r.get("fecha")) for r in raw}
                pers.discard(None)
                if pers:
                    FinancialAnalyzer._API_CACHE["periodos_count"] = len(pers)
        except Exception as e:
            import traceback
            print(f"DEBUG ERROR cartera/moneda: {e}")
            print(traceback.format_exc())
            log.warning("API cartera/moneda falló: %s", e)

        FinancialAnalyzer._API_CACHE[key] = total   # cachear siempre (0.0 si falló)
        return total

    # ── Backend: MySQL o CSV ──────────────────────────────────────────────────
    def _engine_ok(self) -> bool:
        if self._engine:
            return True
        try:
            from src.db.connection import get_engine
            eng = get_engine()
            with eng.connect() as c:
                c.execute(text("SELECT 1"))
            self._engine = eng
            return True
        except Exception:
            return False

    def _query_sql(self, sql: str, params: dict = None) -> pd.DataFrame:
        with self._engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)

    def _csv(self, tabla: str) -> pd.DataFrame:
        if tabla not in self._csv_cache:
            ruta = DATA_DIR / f"{tabla}.csv"
            if not ruta.exists():
                return pd.DataFrame()
            df = pd.read_csv(ruta, parse_dates=["fecha"])
            self._csv_cache[tabla] = df
        return self._csv_cache[tabla].copy()

    def _query(self, tabla: str, sql: str, params: dict = None) -> pd.DataFrame:
        if self._engine_ok():
            try:
                return self._query_sql(sql, params)
            except Exception as e:
                log.warning("SQL falló (%s), usando CSV: %s", tabla, e)
        return self._query_csv(tabla, sql)

    def _query_csv(self, tabla: str, _sql: str) -> pd.DataFrame:
        """Fallback: devuelve el CSV completo (las funciones abajo lo procesan)."""
        return self._csv(tabla)

    # ── Helpers CSV ───────────────────────────────────────────────────────────
    @staticmethod
    def _periodo(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["periodo"] = pd.to_datetime(df["fecha"]).dt.to_period("M").astype(str)
        return df

    # ═══════════════════════════════════════════════════════════════════════════
    #  CAPTACIONES
    # ═══════════════════════════════════════════════════════════════════════════

    def evolucion_captaciones_mensual(self) -> pd.DataFrame:
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo,
                   moneda, SUM(monto) AS total_captado
            FROM captaciones WHERE fuente_endpoint='captaciones_moneda'
              AND moneda != '' AND monto IS NOT NULL
            GROUP BY periodo, moneda ORDER BY periodo
        """
        if self._engine_ok():
            df = self._query_sql(sql)
        else:
            df = self._csv("captaciones")
            df = df[df["fuente_endpoint"] == "captaciones_moneda"]
            df = self._periodo(df)
            df = (df[df["moneda"].ne("")]
                  .groupby(["periodo","moneda"])["monto"].sum()
                  .reset_index(name="total_captado")
                  .sort_values("periodo"))
        if not df.empty:
            df["variacion_pct"] = (df.groupby("moneda")["total_captado"]
                                     .pct_change() * 100)
        return df

    def top_entidades_captaciones(self, n: int = 10) -> pd.DataFrame:
        sql = """
            SELECT entidad, tipo_entidad,
                   SUM(monto) AS total_captado, COUNT(*) AS registros
            FROM captaciones WHERE fuente_endpoint='captaciones_moneda'
              AND monto IS NOT NULL
            GROUP BY entidad, tipo_entidad
            ORDER BY total_captado DESC LIMIT :n
        """
        if self._engine_ok():
            return self._query_sql(sql, {"n": n})
        df = self._csv("captaciones")
        df = df[df["fuente_endpoint"] == "captaciones_moneda"]
        out = (df.groupby(["entidad","tipo_entidad"])["monto"]
                 .sum().reset_index(name="total_captado")
                 .sort_values("total_captado", ascending=False).head(n))
        out["registros"] = 0
        return out

    def distribucion_sector_depositante(self) -> pd.DataFrame:
        sql = """
            SELECT tipo_depositante,
                   SUM(monto) AS total_captado,
                   SUM(monto)*100.0/SUM(SUM(monto)) OVER() AS participacion_pct
            FROM captaciones WHERE fuente_endpoint='captaciones_sector_depositante'
              AND tipo_depositante != '' AND monto IS NOT NULL
            GROUP BY tipo_depositante ORDER BY total_captado DESC
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("captaciones")
        df = df[df["fuente_endpoint"] == "captaciones_sector_depositante"]
        out = (df.groupby("tipo_depositante")["monto"]
                 .sum().reset_index(name="total_captado")
                 .sort_values("total_captado", ascending=False))
        total = out["total_captado"].sum()
        out["participacion_pct"] = out["total_captado"] / total * 100
        return out

    def captaciones_por_localidad(self) -> pd.DataFrame:
        # ── Priority 1: API v2 ────────────────────────────────────────────
        df = self._fetch_captaciones_localidad_api()
        if not df.empty:
            return df
        # ── Priority 2: MySQL ─────────────────────────────────────────────
        sql = """
            SELECT localidad, SUM(monto) AS total_captado
            FROM captaciones WHERE fuente_endpoint='captaciones_localidad'
              AND localidad != '' AND monto IS NOT NULL
            GROUP BY localidad ORDER BY total_captado DESC
        """
        if self._engine_ok():
            return self._query_sql(sql)
        # ── Priority 3: CSV ───────────────────────────────────────────────
        df = self._csv("captaciones")
        df = df[df["fuente_endpoint"] == "captaciones_localidad"]
        return (df.groupby("localidad")["monto"]
                  .sum().reset_index(name="total_captado")
                  .sort_values("total_captado", ascending=False))

    # ═══════════════════════════════════════════════════════════════════════════
    #  CARTERA
    # ═══════════════════════════════════════════════════════════════════════════

    def calidad_cartera(self) -> pd.DataFrame:
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo,
              SUM(CASE WHEN clasificacion_riesgo LIKE 'A%' THEN saldo ELSE 0 END) AS cartera_normal,
              SUM(CASE WHEN clasificacion_riesgo NOT LIKE 'A%' AND clasificacion_riesgo!=''
                       THEN saldo ELSE 0 END) AS cartera_riesgo,
              SUM(saldo) AS total_cartera,
              ROUND(SUM(CASE WHEN clasificacion_riesgo NOT LIKE 'A%' AND clasificacion_riesgo!=''
                              THEN saldo ELSE 0 END)/NULLIF(SUM(saldo),0)*100,2) AS indice_morosidad
            FROM cartera_creditos WHERE fuente_endpoint='cartera_clasificacion_riesgo'
              AND saldo IS NOT NULL
            GROUP BY periodo ORDER BY periodo
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("cartera_creditos")
        df = df[df["fuente_endpoint"] == "cartera_clasificacion_riesgo"].copy()
        df = self._periodo(df)
        grp = df.groupby(["periodo","clasificacion_riesgo"])["saldo"].sum().reset_index()
        piv = grp.pivot_table(index="periodo", columns="clasificacion_riesgo",
                              values="saldo", aggfunc="sum", fill_value=0)
        normal_cols = [c for c in piv.columns if c.startswith("A")]
        risk_cols   = [c for c in piv.columns if not c.startswith("A")]
        out = pd.DataFrame({
            "periodo":          piv.index,
            "cartera_normal":   piv[normal_cols].sum(axis=1).values,
            "cartera_riesgo":   piv[risk_cols].sum(axis=1).values,
        })
        out["total_cartera"]     = out["cartera_normal"] + out["cartera_riesgo"]
        out["indice_morosidad"]  = (out["cartera_riesgo"] / out["total_cartera"] * 100).round(2)
        return out.sort_values("periodo").reset_index(drop=True)

    def cartera_por_sector(self) -> pd.DataFrame:
        sql = """
            SELECT sector_economico, SUM(saldo) AS total_saldo,
                   SUM(numero_deudores) AS total_deudores
            FROM cartera_creditos WHERE fuente_endpoint='cartera_sectores_economicos'
              AND sector_economico != '' AND saldo IS NOT NULL
            GROUP BY sector_economico ORDER BY total_saldo DESC
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("cartera_creditos")
        df = df[df["fuente_endpoint"] == "cartera_sectores_economicos"]
        return (df.groupby("sector_economico")
                  .agg(total_saldo=("saldo","sum"), total_deudores=("numero_deudores","sum"))
                  .reset_index().sort_values("total_saldo", ascending=False))

    def brecha_genero_credito(self) -> pd.DataFrame:
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo, genero,
                   SUM(saldo) AS saldo_total, SUM(numero_deudores) AS total_deudores
            FROM cartera_creditos WHERE fuente_endpoint='cartera_genero'
              AND genero != '' AND saldo IS NOT NULL
            GROUP BY periodo, genero ORDER BY periodo
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("cartera_creditos")
        df = df[df["fuente_endpoint"] == "cartera_genero"]
        df = self._periodo(df)
        return (df[df["genero"].ne("")]
                .groupby(["periodo","genero"])
                .agg(saldo_total=("saldo","sum"), total_deudores=("numero_deudores","sum"))
                .reset_index().sort_values("periodo"))

    def cartera_por_tipo(self) -> pd.DataFrame:
        sql = """
            SELECT tipo_cartera, SUM(saldo) AS total_saldo
            FROM cartera_creditos WHERE fuente_endpoint='cartera_tipo'
              AND tipo_cartera != '' AND saldo IS NOT NULL
            GROUP BY tipo_cartera ORDER BY total_saldo DESC
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("cartera_creditos")
        df = df[df["fuente_endpoint"] == "cartera_tipo"]
        return (df.groupby("tipo_cartera")["saldo"]
                  .sum().reset_index(name="total_saldo")
                  .sort_values("total_saldo", ascending=False))

    # ═══════════════════════════════════════════════════════════════════════════
    #  INDICADORES
    # ═══════════════════════════════════════════════════════════════════════════

    def evolucion_indicadores(self, tipo: str = None) -> pd.DataFrame:
        # ── Priority 1: API v2 ────────────────────────────────────────────
        df = self._fetch_indicadores_api()
        if not df.empty:
            if tipo:
                df = df[df["tipo_indicador"] == tipo]
            return df
        # ── Priority 2: MySQL ─────────────────────────────────────────────
        cond = "AND tipo_indicador=:tipo" if tipo else ""
        sql = f"""
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo, tipo_indicador, nombre,
                   AVG(valor) AS valor_promedio, MIN(valor) AS valor_min,
                   MAX(valor) AS valor_max, STDDEV(valor) AS valor_std
            FROM indicadores WHERE valor IS NOT NULL {cond}
            GROUP BY periodo, tipo_indicador, nombre
            ORDER BY periodo, tipo_indicador
        """
        if self._engine_ok():
            return self._query_sql(sql, {"tipo": tipo} if tipo else {})
        # ── Priority 3: CSV ───────────────────────────────────────────────
        df = self._csv("indicadores")
        df = self._periodo(df)
        if tipo:
            df = df[df["tipo_indicador"] == tipo]
        return (df[df["valor"].notna()]
                .groupby(["periodo","tipo_indicador","nombre"])["valor"]
                .agg(valor_promedio="mean", valor_min="min",
                     valor_max="max", valor_std="std")
                .reset_index().sort_values(["periodo","tipo_indicador"]))

    # ═══════════════════════════════════════════════════════════════════════════
    #  SOLVENCIA
    # ═══════════════════════════════════════════════════════════════════════════

    def solvencia_sistema(self) -> pd.DataFrame:
        # ── Priority 1: API v2 ────────────────────────────────────────────
        df = self._fetch_solvencia_api()
        if not df.empty:
            return df
        # ── Priority 2: MySQL ─────────────────────────────────────────────
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo, componente,
                   AVG(valor) AS promedio, MIN(valor) AS minimo,
                   MAX(valor) AS maximo, COUNT(*) AS entidades
            FROM solvencia WHERE valor IS NOT NULL
            GROUP BY periodo, componente ORDER BY periodo DESC
        """
        if self._engine_ok():
            return self._query_sql(sql)
        # ── Priority 3: CSV ───────────────────────────────────────────────
        df = self._csv("solvencia")
        df = self._periodo(df)
        return (df[df["valor"].notna()]
                .groupby(["periodo","componente"])["valor"]
                .agg(promedio="mean", minimo="min", maximo="max", entidades="count")
                .reset_index().sort_values("periodo", ascending=False))

    def solvencia_por_entidad(self, componente: str = "Índice de Solvencia") -> pd.DataFrame:
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo, entidad, tipo_entidad, valor
            FROM solvencia WHERE componente=:comp AND valor IS NOT NULL
            ORDER BY periodo, entidad
        """
        if self._engine_ok():
            return self._query_sql(sql, {"comp": componente})
        df = self._csv("solvencia")
        df = self._periodo(df)
        return (df[(df["componente"] == componente) & df["valor"].notna()]
                [["periodo","entidad","tipo_entidad","valor"]]
                .sort_values(["periodo","entidad"]))

    # ═══════════════════════════════════════════════════════════════════════════
    #  ESTADOS FINANCIEROS
    # ═══════════════════════════════════════════════════════════════════════════

    def estados_situacion_sistema(self) -> pd.DataFrame:
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo, tipo_entidad,
                   cuenta, descripcion, SUM(monto) AS total_monto
            FROM estados_financieros WHERE tipo_estado='situacion'
              AND monto IS NOT NULL
            GROUP BY periodo, tipo_entidad, cuenta, descripcion
            ORDER BY periodo DESC, total_monto DESC
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("estados_financieros")
        df = self._periodo(df)
        df = df[df["tipo_estado"] == "situacion"]
        return (df.groupby(["periodo","tipo_entidad","cuenta","descripcion"])["monto"]
                  .sum().reset_index(name="total_monto")
                  .sort_values(["periodo","total_monto"], ascending=[False,False]))

    def rentabilidad_serie(self) -> pd.DataFrame:
        sql = """
            SELECT DATE_FORMAT(fecha,'%Y-%m') AS periodo,
                   SUM(CASE WHEN cuenta='99' THEN monto ELSE 0 END) AS resultado_neto,
                   SUM(CASE WHEN cuenta='41' THEN monto ELSE 0 END) AS ingresos_financieros,
                   SUM(CASE WHEN cuenta='1'  THEN monto ELSE 0 END) AS activos_totales
            FROM estados_financieros WHERE tipo_entidad != 'EIC' AND monto IS NOT NULL
            GROUP BY periodo ORDER BY periodo
        """
        if self._engine_ok():
            return self._query_sql(sql)
        df = self._csv("estados_financieros")
        df = self._periodo(df)
        df = df[df["tipo_entidad"] != "EIC"]
        grp = df.groupby(["periodo","cuenta"])["monto"].sum().reset_index()
        piv = grp.pivot_table(index="periodo", columns="cuenta",
                              values="monto", aggfunc="sum", fill_value=0)
        out = pd.DataFrame({"periodo": piv.index})
        out["resultado_neto"]      = piv.get("99", 0)
        out["ingresos_financieros"]= piv.get("41", 0)
        out["activos_totales"]     = piv.get("1",  0)
        return out.sort_values("periodo").reset_index(drop=True)

    # ═══════════════════════════════════════════════════════════════════════════
    #  KPIs GLOBALES
    # ═══════════════════════════════════════════════════════════════════════════

    def resumen_ejecutivo(self) -> dict:
        print("=== DEBUG INICIO ===")
        print(f"API KEY presente: {bool(os.getenv('SB_API_KEY'))}")
        print(f"DATA_DIR existe: {DATA_DIR.exists()} — path: {DATA_DIR}")
        print(f"MySQL disponible: {self._engine_ok()}")

        kpis = {}
        if self._engine_ok():
            print("DEBUG: usando MySQL para KPIs")
            with self._engine.connect() as conn:
                kpis["total_captado_DOP"] = float(
                    conn.execute(text(
                        "SELECT COALESCE(SUM(monto),0) FROM captaciones "
                        "WHERE fuente_endpoint='captaciones_moneda' AND moneda='DOP'"
                    )).scalar() or 0)
                kpis["total_cartera_DOP"] = float(
                    conn.execute(text(
                        "SELECT COALESCE(SUM(saldo),0) FROM cartera_creditos "
                        "WHERE fuente_endpoint='cartera_tipo'"
                    )).scalar() or 0)
                kpis["entidades_unicas"] = int(
                    conn.execute(text(
                        "SELECT COUNT(DISTINCT entidad) FROM captaciones WHERE entidad!=''"
                    )).scalar() or 0)
                kpis["periodos_disponibles"] = int(
                    conn.execute(text(
                        "SELECT COUNT(DISTINCT DATE_FORMAT(fecha,'%Y-%m')) FROM captaciones"
                    )).scalar() or 0)
                kpis["solvencia_promedio"] = float(
                    conn.execute(text(
                        "SELECT AVG(valor) FROM solvencia "
                        "WHERE componente='Índice de Solvencia' "
                        "  AND fecha=(SELECT MAX(fecha) FROM solvencia)"
                    )).scalar() or 0)
                kpis["morosidad_promedio"] = float(
                    conn.execute(text(
                        "SELECT AVG(valor) FROM indicadores "
                        "WHERE nombre='Morosidad Simple' "
                        "  AND fecha=(SELECT MAX(fecha) FROM indicadores)"
                    )).scalar() or 0)
        else:
            print("DEBUG: MySQL no disponible — intentando CSVs")
            cap = self._csv("captaciones")
            car = self._csv("cartera_creditos")
            ind = self._csv("indicadores")
            sol = self._csv("solvencia")
            print(f"DEBUG CSV captaciones: {len(cap)} filas")
            print(f"DEBUG CSV cartera_creditos: {len(car)} filas")
            print(f"DEBUG CSV indicadores: {len(ind)} filas")
            print(f"DEBUG CSV solvencia: {len(sol)} filas")

            csv_tiene_datos = not cap.empty or not car.empty

            if csv_tiene_datos:
                cap_dop = cap[(cap["fuente_endpoint"]=="captaciones_moneda") & (cap["moneda"]=="DOP")] if not cap.empty else cap
                kpis["total_captado_DOP"]    = float(cap_dop["monto"].sum()) if not cap_dop.empty else 0.0
                kpis["total_cartera_DOP"]    = float(car[car["fuente_endpoint"]=="cartera_tipo"]["saldo"].sum()) if not car.empty else 0.0
                kpis["entidades_unicas"]     = int(cap["entidad"].nunique()) if not cap.empty else 0
                kpis["periodos_disponibles"] = int(cap["fecha"].nunique()) if not cap.empty else 0
            else:
                # ── Ruta API: sin MySQL ni CSVs (producción sin ETL) ─────────
                print("DEBUG: CSVs vacíos — usando API para KPIs")
                df_cap_loc = self.captaciones_por_localidad()   # usa caché si ya fue llamado
                kpis["total_captado_DOP"] = float(df_cap_loc["total_captado"].sum()) if not df_cap_loc.empty else 0.0

                kpis["total_cartera_DOP"] = self._fetch_cartera_total_api()

                kpis["entidades_unicas"]     = int(FinancialAnalyzer._API_CACHE.get("entidades_count", 0))
                kpis["periodos_disponibles"] = int(FinancialAnalyzer._API_CACHE.get("periodos_count", 0))

                # Fallback de períodos desde indicadores si captaciones no los reportó
                if kpis["periodos_disponibles"] == 0:
                    df_ind_raw = self._fetch_indicadores_api()
                    if not df_ind_raw.empty:
                        kpis["periodos_disponibles"] = int(df_ind_raw["periodo"].nunique())

                print(f"DEBUG API KPIs: captado={kpis['total_captado_DOP']:.0f}, "
                      f"cartera={kpis['total_cartera_DOP']:.0f}, "
                      f"entidades={kpis['entidades_unicas']}, "
                      f"periodos={kpis['periodos_disponibles']}")

            if not sol.empty:
                ult = sol[sol["componente"]=="Índice de Solvencia"]
                fecha_max = ult["fecha"].max()
                kpis["solvencia_promedio"] = float(ult[ult["fecha"]==fecha_max]["valor"].mean())
            else:
                df_ind2 = self._fetch_indicadores_api()
                if not df_ind2.empty:
                    sol_api = df_ind2[df_ind2["nombre"] == "Índice Solvencia"]
                    kpis["solvencia_promedio"] = float(sol_api["valor_promedio"].iloc[-1]) if not sol_api.empty else 0.0
                else:
                    kpis["solvencia_promedio"] = 0.0

            if not ind.empty:
                mora = ind[ind["nombre"]=="Morosidad Simple"]
                fecha_max = mora["fecha"].max()
                kpis["morosidad_promedio"] = float(mora[mora["fecha"]==fecha_max]["valor"].mean())
            else:
                df_ind2 = self._fetch_indicadores_api()
                if not df_ind2.empty:
                    mora_api = df_ind2[df_ind2["nombre"] == "Morosidad Simple"]
                    kpis["morosidad_promedio"] = float(mora_api["valor_promedio"].iloc[-1]) if not mora_api.empty else 0.0
                else:
                    kpis["morosidad_promedio"] = 0.0

        print(f"DEBUG KPIs resultado: {kpis}")
        print("=== DEBUG FIN ===")
        return kpis

    def estadisticas_descriptivas(self) -> dict:
        resultados = {}
        tablas = {
            "captaciones":          ("monto",  "captaciones_moneda"),
            "cartera_creditos":     ("saldo",   "cartera_tipo"),
            "indicadores":          ("valor",   None),
            "solvencia":            ("valor",   None),
        }
        for tabla, (col, endpoint) in tablas.items():
            if self._engine_ok():
                cond = f"AND fuente_endpoint='{endpoint}'" if endpoint else ""
                df = self._query_sql(
                    f"SELECT {col} AS valor FROM {tabla} WHERE {col} IS NOT NULL {cond}")
            else:
                df = self._csv(tabla)
                if endpoint and "fuente_endpoint" in df.columns:
                    df = df[df["fuente_endpoint"] == endpoint]
                df = df[[col]].rename(columns={col: "valor"}).dropna()

            if not df.empty:
                s = df["valor"].describe(percentiles=[.1,.25,.5,.75,.9,.95])
                s["skewness"] = df["valor"].skew()
                s["kurtosis"] = df["valor"].kurt()
                resultados[tabla] = s.to_dict()
        return resultados

    # ═══════════════════════════════════════════════════════════════════════════
    #  ANÁLISIS AVANZADO
    # ═══════════════════════════════════════════════════════════════════════════

    def correlacion_macro_banca(self) -> pd.DataFrame:
        """Matriz de correlación cruzada entre variables macro y bancarias."""
        import pathlib as _pl
        DATA = _pl.Path(__file__).parent.parent.parent / "data" / "processed"
        frames = {}

        for fname, col, alias in [
            ("macro_tasas.csv",      "tpm_nominal",        "TPM"),
            ("macro_inflacion.csv",  "ipc_interanual_pct", "IPC"),
            ("macro_tipo_cambio.csv","venta_dop_usd",      "TC DOP/USD"),
            ("macro_remesas.csv",    "monto_usd_millones", "Remesas"),
        ]:
            p = DATA / fname
            if p.exists():
                d = pd.read_csv(p, parse_dates=["fecha"])
                d["periodo"] = d["fecha"].dt.to_period("M").astype(str)
                frames[alias] = d.groupby("periodo")[col].mean()

        # Morosidad mensual
        df_car = self._csv("cartera_creditos")
        if not df_car.empty:
            df_car = df_car[df_car["fuente_endpoint"] == "cartera_clasificacion_riesgo"].copy()
            df_car["periodo"] = pd.to_datetime(df_car["fecha"]).dt.to_period("M").astype(str)
            grp = df_car.groupby(["periodo","clasificacion_riesgo"])["saldo"].sum().reset_index()
            total = grp.groupby("periodo")["saldo"].sum()
            normal = grp[grp["clasificacion_riesgo"].str.startswith("A", na=False)].groupby("periodo")["saldo"].sum()
            mora = ((total - normal.reindex(total.index, fill_value=0)) / total * 100)
            frames["Morosidad"] = mora

        # Captaciones mensuales
        df_cap = self._csv("captaciones")
        if not df_cap.empty:
            df_cap = df_cap[df_cap["fuente_endpoint"] == "captaciones_moneda"].copy()
            df_cap["periodo"] = pd.to_datetime(df_cap["fecha"]).dt.to_period("M").astype(str)
            frames["Captaciones"] = df_cap.groupby("periodo")["monto"].sum()

        if len(frames) < 2:
            return pd.DataFrame()

        merged = pd.DataFrame(frames).dropna()
        return merged.corr().round(4)

    def histograma_datos(self, tabla: str = "captaciones",
                         col: str = "monto", bins: int = 50) -> pd.DataFrame:
        """Devuelve frecuencias y límites de bins para histograma interactivo."""
        if self._engine_ok():
            cond = "AND fuente_endpoint='captaciones_moneda'" if tabla == "captaciones" else ""
            df = self._query_sql(
                f"SELECT {col} FROM {tabla} WHERE {col} IS NOT NULL {cond} LIMIT 100000")
            series = df[col]
        else:
            df = self._csv(tabla)
            if tabla == "captaciones" and "fuente_endpoint" in df.columns:
                df = df[df["fuente_endpoint"] == "captaciones_moneda"]
            series = df[col].dropna()

        if series.empty:
            return pd.DataFrame()
        counts, edges = np.histogram(series, bins=bins)
        return pd.DataFrame({
            "bin_left":  edges[:-1],
            "bin_right": edges[1:],
            "frecuencia": counts,
            "bin_mid":   (edges[:-1] + edges[1:]) / 2,
        })

    def detectar_outliers(self, tabla: str = "captaciones",
                          col: str = "monto") -> pd.DataFrame:
        """IQR + Z-score para detección de outliers."""
        if self._engine_ok():
            cond = "AND fuente_endpoint='captaciones_moneda'" if tabla == "captaciones" else ""
            df = self._query_sql(
                f"SELECT entidad, fecha, {col} FROM {tabla} "
                f"WHERE {col} IS NOT NULL {cond} LIMIT 200000")
        else:
            df = self._csv(tabla)
            if tabla == "captaciones" and "fuente_endpoint" in df.columns:
                df = df[df["fuente_endpoint"] == "captaciones_moneda"]
            df = df[["entidad", "fecha", col]].dropna()

        if df.empty:
            return pd.DataFrame()

        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        mu, sigma = df[col].mean(), df[col].std()

        df = df.copy()
        df["z_score"]    = ((df[col] - mu) / sigma).abs()
        df["iqr_outlier"] = (df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)
        df["z_outlier"]   = df["z_score"] > 3.0
        df["outlier"]     = df["iqr_outlier"] | df["z_outlier"]
        return df[df["outlier"]].sort_values(col, ascending=False).head(200)
