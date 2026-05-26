"""Lanzador directo del dashboard — sin chequeo de API key."""
import sys, os
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

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
