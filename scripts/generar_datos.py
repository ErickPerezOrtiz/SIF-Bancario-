#!/usr/bin/env python3
"""
Genera CSVs pre-calculados desde la API de la Superintendencia de Bancos RD.

Ejecutar UNA VEZ localmente con la API key configurada en .env:
    python scripts/generar_datos.py

Los CSVs resultantes se suben a GitHub y la app los usa en producción
sin necesidad de llamar la API en vivo.
"""
import sys
import os
import pathlib
import time

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import pandas as pd

DATA_DIR = ROOT / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _save(df: pd.DataFrame, filename: str, label: str) -> bool:
    if df is None or (hasattr(df, "empty") and df.empty):
        print(f"  SKIP {label}: sin datos")
        return False
    path = DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  OK   {label}: {len(df)} filas → {filename}")
    return True


def main():
    t0 = time.time()
    print("=" * 62)
    print("  GENERADOR DE CSVs — SIF-BANCARIO")
    print(f"  Destino: {DATA_DIR}")
    print("=" * 62)

    api_key = os.environ.get("SB_API_KEY", "")
    if not api_key:
        print("\nERROR: SB_API_KEY no encontrada. Configura .env antes de continuar.")
        sys.exit(1)
    print(f"\nAPI key: {api_key[:4]}...{api_key[-4:]}")

    from src.analysis.statistics import FinancialAnalyzer
    az = FinancialAnalyzer()

    # ── 1. Indicadores (financieros + principales + morosidad estresada) ───────
    print("\n[1/5] indicadores/financieros + principales + morosidad-estresada")
    df_ind = az._fetch_indicadores_api()
    _save(df_ind, "cache_indicadores.csv", "indicadores")

    # ── 2. Solvencia ──────────────────────────────────────────────────────────
    print("\n[2/5] solvencia/componentes")
    df_sol = az._fetch_solvencia_api()
    _save(df_sol, "cache_solvencia.csv", "solvencia")

    # ── 3. Captaciones por localidad ──────────────────────────────────────────
    print("\n[3/5] captaciones/localidad")
    df_cap = az._fetch_captaciones_localidad_api()
    _save(df_cap, "cache_captaciones_localidad.csv", "captaciones localidad")

    # ── 4. Cartera total + meta ───────────────────────────────────────────────
    print("\n[4/5] carteras/creditos/moneda (total KPI)")
    total_cartera = az._fetch_cartera_total_api()
    entidades = FinancialAnalyzer._API_CACHE.get("entidades_count", 0)
    periodos  = FinancialAnalyzer._API_CACHE.get("periodos_count", 0)
    meta_df = pd.DataFrame([{
        "cartera_total_dop": total_cartera,
        "entidades_count":   entidades,
        "periodos_count":    periodos,
    }])
    meta_df.to_csv(DATA_DIR / "cache_meta.csv", index=False)
    print(f"  OK   meta: cartera={total_cartera:,.0f}  entidades={entidades}  periodos={periodos}")

    # ── 5. Series macroeconómicas BCRD (datos sintéticos calibrados) ──────────
    print("\n[5/5] Series macro BCRD (TPM, IPC, tipo de cambio, remesas)")
    from src.macro.bcrd_data import generar_macro_completo, guardar_macro_csv
    macro_dfs = generar_macro_completo()
    guardar_macro_csv(macro_dfs)
    for nombre, df in macro_dfs.items():
        print(f"  OK   {nombre}: {len(df)} filas")

    elapsed = time.time() - t0
    print(f"\n{'='*62}")
    print(f"  Completado en {elapsed:.0f}s")
    print(f"  CSVs en: {DATA_DIR}")
    print(f"  Siguiente paso:")
    print(f"    git add data/processed/ && git commit -m 'data: static CSVs' && git push")
    print(f"{'='*62}")


if __name__ == "__main__":
    main()
