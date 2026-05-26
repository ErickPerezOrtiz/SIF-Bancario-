"""Lanzador directo del dashboard — sin chequeo de API key."""
import sys, os, pathlib
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

# ── Diagnóstico API key ───────────────────────────────────────────────────────
_key = os.environ.get("SB_API_KEY", "")
if _key:
    print(f"SB_API_KEY: SET ({_key[:4]}…{_key[-4:]})")
else:
    print("SB_API_KEY: NOT SET — las llamadas a la API fallarán")

# ── Generar CSVs macro si no existen (Render tiene filesystem efímero) ────────
_DATA_DIR = pathlib.Path("data/processed")
_MACRO_FILES = [
    "macro_tasas.csv", "macro_inflacion.csv", "macro_tipo_cambio.csv",
    "macro_pib.csv",   "macro_remesas.csv",
]
if not all((_DATA_DIR / f).exists() for f in _MACRO_FILES):
    print("Generando datos macro BCRD (primera vez o filesystem efímero)…")
    from src.macro.bcrd_data import generar_macro_completo, guardar_macro_csv
    guardar_macro_csv(generar_macro_completo())
    print("Datos macro generados y guardados.")

from src.dashboard.app import create_app
from config.settings import DASH_HOST, DASH_PORT

# Render.com inyecta PORT como variable de entorno; respetar si existe
port = int(os.environ.get("PORT", DASH_PORT))

app = create_app()
print(f"\n{'='*55}")
print(f"  SIF-Bancario Dashboard")
print(f"  http://localhost:{port}")
print(f"  Ctrl+C para detener")
print(f"{'='*55}\n")
app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
