"""Cliente HTTP para la API de Estadísticas del Sistema Financiero — SB-RD.

Base URL: https://apis.sb.gob.do/estadisticas/
Auth header: Ocp-Apim-Subscription-Key
Params: periodoInicial (YYYY-MM), periodoFinal (YYYY-MM), entidad, tipoEntidad
"""
import json as _json
import time
import logging
import requests
from typing import Optional
from config.settings import BASE_URL, BASE_URL_V2, API_HEADERS, REQUEST_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)


class SBApiClient:
    """Consume la API REST de la Superintendencia de Bancos de la RD."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(API_HEADERS)
        self.base_url = BASE_URL.rstrip("/")

    def _request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as e:
                code = resp.status_code
                if code == 401:
                    logger.error("API Key inválida. Verifica tu Ocp-Apim-Subscription-Key.")
                    raise
                if code == 403:
                    logger.error("Acceso denegado (403) en %s. Verifica suscripción activa.", url)
                    raise
                if code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limit. Esperando %ds...", wait)
                    time.sleep(wait)
                else:
                    logger.error("HTTP %s en %s: %s", code, url, e)
                    if attempt == MAX_RETRIES:
                        raise
            except requests.exceptions.ConnectionError:
                logger.error("No se pudo conectar a %s", url)
                if attempt == MAX_RETRIES:
                    raise
            except Exception as e:
                logger.error("Error inesperado en %s: %s", url, e)
                if attempt == MAX_RETRIES:
                    raise
        return None

    def get_all(self, endpoint: str, params: dict = None) -> list:
        """Descarga todos los registros de un endpoint (sin paginación — la API devuelve todo)."""
        params = params or {}
        data = self._request(endpoint, params)
        if data is None:
            return []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("data", data.get("registros", data.get("items", [])))
            if not isinstance(records, list):
                records = [data]
        else:
            records = []
        logger.info("  %-45s → %d registros", endpoint, len(records))
        return records

    # ── Captaciones ──────────────────────────────────────────────────────────
    def captaciones_localidad(self, **kw):
        return self.get_all("captaciones/localidad", kw)

    def captaciones_moneda(self, **kw):
        return self.get_all("captaciones/moneda", kw)

    def captaciones_sector_depositante(self, **kw):
        return self.get_all("captaciones/sector-depositante", kw)

    # ── Cartera de Créditos ───────────────────────────────────────────────────
    def cartera_clasificacion_riesgo(self, **kw):
        return self.get_all("carteras/creditos/clasificacion-riesgo", kw)

    def cartera_genero(self, **kw):
        return self.get_all("carteras/creditos/genero", kw)

    def cartera_localidad(self, **kw):
        return self.get_all("carteras/creditos/localidad", kw)

    def cartera_moneda(self, **kw):
        return self.get_all("carteras/creditos/moneda", kw)

    def cartera_sectores_economicos(self, **kw):
        return self.get_all("carteras/creditos/sectores-economicos", kw)

    def cartera_tipo(self, **kw):
        return self.get_all("carteras/creditos/tipo", kw)

    def cartera_facilidad(self, **kw):
        return self.get_all("carteras/creditos/facilidad", kw)

    def cartera_inversiones(self, **kw):
        return self.get_all("carteras/creditos/inversiones", kw)

    # ── Estados Financieros ──────────────────────────────────────────────────
    def estados_resultados_eif(self, **kw):
        return self.get_all("estados/resultados/eif", kw)

    def estados_resultados_eic(self, **kw):
        return self.get_all("estados/resultados/eic", kw)

    def estados_situacion_eif(self, **kw):
        return self.get_all("estados/situacion/eif", kw)

    def estados_situacion_eic(self, **kw):
        return self.get_all("estados/situacion/eic", kw)

    # ── Indicadores ──────────────────────────────────────────────────────────
    def indicadores_morosidad_estresada(self, **kw):
        return self.get_all("indicadores/morosidad-estresada", kw)

    def indicadores_riesgo_credito(self, **kw):
        return self.get_all("indicadores/riesgo-credito", kw)

    def indicadores_financieros(self, **kw):
        return self.get_all("indicadores/financieros", kw)

    def indicadores_principales(self, **kw):
        return self.get_all("indicadores/principales", kw)

    # ── Solvencia ────────────────────────────────────────────────────────────
    def solvencia_componentes(self, **kw):
        return self.get_all("solvencia/componentes", kw)

    # ── Otros ────────────────────────────────────────────────────────────────
    def detalle_entidades_acceso(self, **kw):
        return self.get_all("detalle-entidades/acceso", kw)

    def reclamaciones_eif(self, **kw):
        return self.get_all("reclamaciones/eif", kw)

    def tasas_comisiones_tarjetas(self, **kw):
        return self.get_all("tasas-comisiones/tarjetas-credito", kw)

    def test_connection(self) -> bool:
        """Verifica que la API Key y la URL funcionen."""
        try:
            r = self._request("captaciones/moneda", {"periodoInicial": "2024-01", "periodoFinal": "2024-01"})
            if r is not None:
                logger.info("Conexión a la API de SB-RD exitosa.")
                return True
        except Exception:
            pass
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  Cliente v2 — paginación automática via header x-pagination
# ══════════════════════════════════════════════════════════════════════════════

class SBApiClientV2:
    """
    Cliente HTTP para la API v2 de Estadísticas SB-RD.

    Maneja paginación automática usando el header ``x-pagination``::

        {"HasNext": true/false, "TotalCount": N, "PageSize": M, ...}

    Loop: hace GET con paginas=1, 2, 3... hasta que HasNext==False o respuesta vacía.
    """

    PERIODO_INICIAL = "2015-01"
    PERIODO_FINAL   = "2025-12"
    TIPO_ENTIDAD    = "BM"       # Bancos Múltiples por defecto
    PAGE_SIZE       = 500

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(API_HEADERS)
        self.base_url = BASE_URL_V2.rstrip("/")

    def _paginate(self, endpoint: str, params: dict) -> list:
        """Loop de paginación via x-pagination header. Compartido por todos los fetchers."""
        url      = f"{self.base_url}/{endpoint.lstrip('/')}"
        all_data: list = []
        page     = 1

        while True:
            params["paginas"] = page
            try:
                resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error("HTTP %s en %s p.%d", resp.status_code, endpoint, page)
                break
            except Exception as e:
                logger.error("Error en %s p.%d: %s", endpoint, page, e)
                break

            try:
                body = resp.json()
            except Exception:
                logger.error("Respuesta no-JSON en %s p.%d", endpoint, page)
                break

            if isinstance(body, list):
                records = body
            elif isinstance(body, dict):
                records = body.get("data",
                           body.get("registros",
                           body.get("items", [])))
                if not isinstance(records, list):
                    records = [body] if body else []
            else:
                records = []

            all_data.extend(records)

            has_next = False
            raw_pag = resp.headers.get("x-pagination", "")
            if raw_pag:
                try:
                    pag = _json.loads(raw_pag)
                    has_next = bool(pag.get("HasNext", pag.get("hasNext", False)))
                except Exception:
                    pass

            if not has_next or not records:
                break
            page += 1

        logger.info("v2 %-42s → %d registros (%d págs)", endpoint, len(all_data), page)
        return all_data

    def _get_all_pages(self, endpoint: str, extra_params: dict = None) -> list:
        """Paginador con tipoEntidad=BM y PAGE_SIZE=500 (para endpoints de bajo volumen)."""
        params = {
            "periodoInicial": self.PERIODO_INICIAL,
            "periodoFinal":   self.PERIODO_FINAL,
            "tipoEntidad":    self.TIPO_ENTIDAD,
            "registros":      self.PAGE_SIZE,
        }
        if extra_params:
            params.update(extra_params)
        return self._paginate(endpoint, params)

    def _get_todos_pages(self, endpoint: str, extra_params: dict = None) -> list:
        """
        Paginador con entidad=TODOS y registros=5000.

        La API no admite tipoEntidad y entidad simultáneamente; al usar
        entidad=TODOS se recuperan los agregados del sistema para TODOS los
        tipos de entidad, pero con 5000 registros/página el volumen de páginas
        se reduce de ~393 a ~12 para indicadores/financieros (2x más rápido).
        Filtrar a tipoEntidad="BANCOS MÚLTIPLES" en el consumidor si se necesita.
        """
        params = {
            "periodoInicial": self.PERIODO_INICIAL,
            "periodoFinal":   self.PERIODO_FINAL,
            "entidad":        "TODOS",
            "registros":      5000,
        }
        if extra_params:
            params.update(extra_params)
        return self._paginate(endpoint, params)

    # ── Endpoints requeridos ─────────────────────────────────────────────────

    def indicadores_financieros(self, **kw) -> list:
        # tipoEntidad=BM + registros=500 = 393 páginas; TODOS + 5000 = 12 páginas
        return self._get_todos_pages("indicadores/financieros", kw)

    def indicadores_morosidad_estresada(self, **kw) -> list:
        return self._get_all_pages("indicadores/morosidad-estresada", kw)

    def indicadores_principales(self, **kw) -> list:
        return self._get_all_pages("indicadores/principales", kw)

    def solvencia(self, **kw) -> list:
        # /solvencia devuelve 404 en v2; TODOS + 5000 = 2 páginas vs 43 con BM+500
        return self._get_todos_pages("solvencia/componentes", kw)

    def captaciones_localidad(self, **kw) -> list:
        return self._get_all_pages("captaciones/localidad", kw)

    def cartera_moneda(self, **kw) -> list:
        return self._get_all_pages("carteras/creditos/moneda", kw)
