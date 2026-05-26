"""Configuración central del proyecto SIF-Bancario."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API ──────────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("SB_API_KEY") or os.getenv("API_KEY_SB", "")
BASE_URL     = os.getenv("SB_BASE_URL",    "https://apis.sb.gob.do/estadisticas")
BASE_URL_V2  = os.getenv("SB_BASE_URL_V2", "https://apis.sb.gob.do/estadisticas/v2")
API_HEADERS  = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://desarrollador.sb.gob.do/",
    "Origin": "https://desarrollador.sb.gob.do",
}
REQUEST_TIMEOUT = 30
MAX_RETRIES     = 3

# ── Base de datos ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME", "sif_bancario"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ── Dashboard ─────────────────────────────────────────────────────────────────
DASH_HOST  = os.getenv("DASH_HOST", "0.0.0.0")
DASH_PORT  = int(os.getenv("DASH_PORT", 8050))
DASH_DEBUG = os.getenv("DASH_DEBUG", "False").lower() == "true"

# ── ETL ───────────────────────────────────────────────────────────────────────
LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")

# ── Endpoints reales (fuente: github.com/Lien3105/supeRbancos) ────────────────
ENDPOINTS = {
    # Captaciones
    "captaciones_localidad":            "captaciones/localidad",
    "captaciones_moneda":               "captaciones/moneda",
    "captaciones_sector_depositante":   "captaciones/sector-depositante",
    # Cartera de créditos
    "cartera_clasificacion_riesgo":     "carteras/creditos/clasificacion-riesgo",
    "cartera_genero":                   "carteras/creditos/genero",
    "cartera_localidad":                "carteras/creditos/localidad",
    "cartera_moneda":                   "carteras/creditos/moneda",
    "cartera_sectores_economicos":      "carteras/creditos/sectores-economicos",
    "cartera_tipo":                     "carteras/creditos/tipo",
    "cartera_facilidad":                "carteras/creditos/facilidad",
    "cartera_inversiones":              "carteras/creditos/inversiones",
    # Estados financieros
    "estados_resultados_eif":           "estados/resultados/eif",
    "estados_resultados_eic":           "estados/resultados/eic",
    "estados_situacion_eif":            "estados/situacion/eif",
    "estados_situacion_eic":            "estados/situacion/eic",
    # Indicadores
    "indicadores_morosidad_estresada":  "indicadores/morosidad-estresada",
    "indicadores_riesgo_credito":       "indicadores/riesgo-credito",
    "indicadores_financieros":          "indicadores/financieros",
    "indicadores_principales":          "indicadores/principales",
    # Solvencia
    "solvencia_componentes":            "solvencia/componentes",
    # Acceso financiero
    "detalle_entidades_acceso":         "detalle-entidades/acceso",
    # Reclamaciones
    "reclamaciones_eif":                "reclamaciones/eif",
    "reclamaciones_prousuario":         "reclamaciones/prousuario",
    # Subagentes
    "subagentes_operaciones":           "subagentes/operaciones",
    "subagentes_actividad_economica":   "subagentes/actividad-economica",
    "subagentes_total":                 "subagentes/total",
    # Tasas y comisiones
    "tasas_comisiones_tarjetas":        "tasas-comisiones/tarjetas-credito",
}

EIF_TYPES  = ["BA", "BM", "CA", "CF", "CM"]
CURRENCIES = ["DOP", "USD", "EUR"]
