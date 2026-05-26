"""
Sistema de Inteligencia Financiera — Banca Dominicana
Portafolio de Erick Pérez · Analítica y Ciencia de Datos · ITLA
"""
import sys
import os
import logging
import argparse
import colorlog

# Asegura que el raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import LOG_LEVEL, API_KEY


def setup_logging():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        }
    ))
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, "INFO"), handlers=[handler])


def cmd_etl(_):
    from src.db.connection import create_database_if_not_exists
    from src.etl.pipeline import ETLPipeline
    create_database_if_not_exists()
    etl = ETLPipeline()
    resultados = etl.run_all()
    print("\n📊 Resultados del pipeline ETL:")
    for k, v in resultados.items():
        print(f"  {k:<30} {v:>8,} registros")


def cmd_dashboard(_):
    from src.dashboard.app import run
    run()


def cmd_test_api(_):
    from src.api.client import SBApiClient
    client = SBApiClient()
    ok = client.test_connection()
    if ok:
        print("✅  Conexión a la API de SB-RD exitosa.")
    else:
        print("❌  No se pudo conectar. Revisa tu API key en el archivo .env")
        sys.exit(1)


def cmd_stats(_):
    from src.analysis.statistics import FinancialAnalyzer
    az = FinancialAnalyzer()
    stats = az.estadisticas_descriptivas()
    for tabla, s in stats.items():
        print(f"\n{'─'*50}")
        print(f"  {tabla.upper()}")
        print(f"{'─'*50}")
        for k, v in s.items():
            print(f"  {k:<20} {v:>15,.4f}" if isinstance(v, float) else f"  {k:<20} {v}")


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    if not API_KEY:
        logger.error(
            "❌  API Key no configurada.\n"
            "    1. Copia .env.example → .env\n"
            "    2. Ingresa tu Ocp-Apim-Subscription-Key en SB_API_KEY\n"
            "    Regístrate en: https://desarrollador.sb.gob.do"
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="SIF-Bancario — Sistema de Inteligencia Financiera Banca Dominicana"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("etl",       help="Ejecuta el pipeline ETL completo (API → MySQL)")
    sub.add_parser("dashboard", help="Lanza el dashboard interactivo en Plotly Dash")
    sub.add_parser("test-api",  help="Verifica la conexión y la API Key")
    sub.add_parser("stats",     help="Muestra estadísticas descriptivas en consola")

    args = parser.parse_args()
    cmds = {
        "etl":       cmd_etl,
        "dashboard": cmd_dashboard,
        "test-api":  cmd_test_api,
        "stats":     cmd_stats,
    }
    cmds[args.cmd](args)


if __name__ == "__main__":
    main()
