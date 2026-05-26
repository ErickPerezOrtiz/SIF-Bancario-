"""
Generador de datos de muestra — Sistema Financiero Dominicano
Dataset sintético con magnitudes realistas. Período: 2015-01 – 2025-12 (132 meses)
Patrones macroeconómicos reales de RD incorporados en cada serie.
"""
import sys, os, logging
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)
rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════════════════════════════════════
#  CATÁLOGOS DE ENTIDADES
# ═══════════════════════════════════════════════════════════════════════════════
BANCOS_MULTIPLES = [
    ("Banco Popular Dominicano", "BM", 0.230),
    ("Banco de Reservas",        "BM", 0.210),
    ("BHD León",                 "BM", 0.150),
    ("Scotiabank RD",            "BM", 0.080),
    ("Banesco",                  "BM", 0.060),
    ("Citibank RD",              "BM", 0.040),
    ("Banco Santa Cruz",         "BM", 0.030),
    ("Banco López de Haro",      "BM", 0.030),
    ("JMMB Bank",                "BM", 0.030),
    ("Banco Vimenca",            "BM", 0.020),
    ("Banco del Progreso",       "BM", 0.020),
    ("Caribe Express Banco",     "BM", 0.020),
]
ASOCIACIONES = [
    ("Asociación Popular de Ahorros y Préstamos", "CA", 0.40),
    ("Asociación Cibao",                          "CA", 0.25),
    ("La Nacional",                               "CA", 0.15),
    ("Romana",                                    "CA", 0.10),
    ("Mocana",                                    "CA", 0.10),
]
BANCOS_AHORRO = [
    ("ADOPEM",        "BA", 0.35),
    ("Bancamérica",   "BA", 0.30),
    ("Banfond",       "BA", 0.20),
    ("Motor Crédito", "BA", 0.15),
]
TODAS_ENTIDADES = BANCOS_MULTIPLES + ASOCIACIONES + BANCOS_AHORRO
PESO_TIPO = {"BM": 1.0, "CA": 0.12, "BA": 0.05}

MONEDAS    = [("DOP", 0.72), ("USD", 0.27), ("EUR", 0.01)]
PROVINCIAS = [
    ("Santo Domingo",        0.32), ("Santiago",             0.17),
    ("La Altagracia",        0.08), ("San Pedro de Macorís", 0.06),
    ("La Vega",              0.05), ("San Cristóbal",        0.05),
    ("Puerto Plata",         0.04), ("Espaillat",            0.03),
    ("Duarte",               0.03), ("Peravia",              0.02),
    ("Barahona",             0.02), ("Azua",                 0.02),
    ("La Romana",            0.02), ("Otras provincias",     0.09),
]
SECTORES_DEPOSITANTES = [
    ("Hogares",                   0.38), ("Empresas privadas",         0.30),
    ("Empresas públicas",         0.10), ("Gobierno central",          0.08),
    ("Instituciones financieras", 0.07), ("ONGs y asociaciones",       0.04),
    ("No residentes",             0.03),
]
SECTORES_ECONOMICOS = [
    ("Comercio",                    0.22), ("Consumo personal",            0.20),
    ("Construcción e inmobiliario", 0.15), ("Manufactura",                 0.10),
    ("Turismo y hotelería",         0.09), ("Agropecuario",                0.06),
    ("Transporte y logística",      0.05), ("Salud",                       0.04),
    ("Educación",                   0.04), ("Gobierno",                    0.03),
    ("Otros",                       0.02),
]
CLASIFICACIONES_RIESGO = [
    ("A - Normal",            0.82), ("B - Mención especial", 0.08),
    ("C - Subestándar",       0.04), ("D - Dudoso",           0.03),
    ("E - Irrecuperable",     0.03),
]
TIPOS_CARTERA = [
    ("Comercial", 0.42), ("Consumo", 0.30), ("Hipotecario", 0.20), ("Microcrédito", 0.08),
]
CUENTAS_SITUACION = [
    ("1",  "ACTIVOS TOTALES",                     1.000),
    ("11", "Disponibilidades",                    0.180),
    ("12", "Inversiones en valores",              0.120),
    ("13", "Cartera de créditos neta",            0.440),
    ("14", "Cuentas por cobrar",                  0.030),
    ("15", "Activos fijos netos",                 0.040),
    ("16", "Otros activos",                       0.080),
    ("2",  "PASIVOS TOTALES",                     0.870),
    ("21", "Depósitos del público",               0.680),
    ("22", "Préstamos de instituciones financ.",  0.090),
    ("23", "Valores en circulación",              0.050),
    ("24", "Otros pasivos",                       0.050),
    ("3",  "PATRIMONIO NETO",                     0.130),
    ("31", "Capital pagado",                      0.060),
    ("32", "Reservas de capital",                 0.040),
    ("33", "Resultados acumulados",               0.030),
]
CUENTAS_RESULTADOS = [
    ("41",  "Ingresos financieros",               0.090),
    ("411", "Intereses cartera de créditos",      0.065),
    ("412", "Ingresos por inversiones",           0.020),
    ("51",  "Gastos financieros",                 0.045),
    ("511", "Intereses depósitos del público",    0.030),
    ("61",  "Margen financiero bruto",            0.045),
    ("71",  "Provisiones por incobrabilidad",     0.008),
    ("91",  "Gastos operativos",                  0.028),
    ("92",  "Gastos de personal",                 0.015),
    ("99",  "Resultado neto del período",         0.018),
]
INDICADORES = [
    ("ROA",                      "principales", 0.018, 0.003),
    ("ROE",                      "principales", 0.165, 0.025),
    ("Eficiencia Operacional",   "principales", 0.52,  0.05),
    ("Liquidez Inmediata",       "principales", 0.22,  0.04),
    ("Cobertura de Cartera",     "principales", 1.45,  0.20),
    ("Margen de Intermediación", "financieros", 0.085, 0.008),
    ("Spread Tasas de Interés",  "financieros", 0.072, 0.007),
    ("Activos Improductivos",    "financieros", 0.038, 0.006),
    ("Apalancamiento",           "financieros", 8.50,  0.80),
    ("Morosidad Simple",         "morosidad",   0.018, 0.004),
    ("Morosidad Estresada",      "morosidad",   0.028, 0.005),
    ("Índice Riesgo Crédito",    "morosidad",   0.022, 0.004),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  CALENDARIO Y FACTOR MACRO REALISTA DE RD 2015-2025
# ═══════════════════════════════════════════════════════════════════════════════

INICIO = date(2015, 1, 1)
FIN    = date(2025, 12, 1)

def generar_periodos():
    p, periodos = INICIO, []
    while p <= FIN:
        periodos.append(p)
        p += relativedelta(months=1)
    return periodos   # 132 meses

def _t(periodo: date) -> int:
    """Meses desde el inicio."""
    return (periodo.year - INICIO.year) * 12 + (periodo.month - INICIO.month)

def factor_crecimiento(periodo: date) -> float:
    """
    Factor de escala acumulado (relativo a 2015-01 = 1.0).
    Refleja el crecimiento real del sistema bancario dominicano.
    """
    t = _t(periodo)

    # Tendencia base: sistema crece ~10% anual nominal (5% real + 5% inflación)
    trend = (1.10) ** (t / 12)

    # COVID: shock Mar–Ago 2020, recuperación Sep 2020 – Jun 2021
    if date(2020, 3, 1) <= periodo <= date(2020, 8, 1):
        meses_covid = (periodo.year - 2020) * 12 + (periodo.month - 3)
        shock = 0.92 + 0.013 * meses_covid          # cae hasta 0.92, recupera
    elif date(2020, 9, 1) <= periodo <= date(2021, 6, 1):
        meses_rec = (periodo.year - 2020) * 12 + (periodo.month - 9)
        shock = 0.98 + 0.004 * meses_rec
    else:
        shock = 1.0

    # 2022: expansión crediticia por inflación
    boom_2022 = 1.06 if date(2022, 1, 1) <= periodo <= date(2022, 12, 1) else 1.0

    # Estacionalidad: Q4 alto (dic), Q1 bajo (ene)
    estacional = 1 + 0.018 * np.sin(2 * np.pi * (periodo.month - 3) / 12)

    return trend * shock * boom_2022 * estacional

def morosidad_base(periodo: date) -> float:
    """Morosidad base del sistema según período macroeconómico."""
    # 2015-2019: descendente (6% → 1.6%)
    if periodo < date(2020, 1, 1):
        t = _t(periodo)
        return max(0.016, 0.060 - 0.0037 * t)
    # COVID shock: sube a ~3%
    elif date(2020, 3, 1) <= periodo <= date(2021, 3, 1):
        meses = (periodo.year - 2020) * 12 + (periodo.month - 3)
        peak = min(meses / 4, 1.0)
        return 0.018 + 0.012 * peak
    # Recuperación 2021-2022
    elif date(2021, 4, 1) <= periodo <= date(2022, 12, 1):
        meses = (periodo.year - 2021) * 12 + (periodo.month - 4)
        return 0.030 - 0.0008 * meses
    # 2023-2025: normalización ~1.7%
    else:
        return 0.017 + rng.normal(0, 0.001)

def _ruido(n=1, sigma=0.04):
    return rng.normal(1.0, sigma, n)

# ═══════════════════════════════════════════════════════════════════════════════
#  GENERADORES DE TABLAS BANCARIAS
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVOS_BASE_2015 = 900_000   # millones DOP — sistema bancario 2015 total

def generar_captaciones(periodos):
    log.info("Generando captaciones (132 meses × 21 entidades × 3 desgloses)...")
    rows = []
    for periodo in periodos:
        fc = factor_crecimiento(periodo)
        for nombre, tipo, peso in TODAS_ENTIDADES:
            monto_total = ACTIVOS_BASE_2015 * 0.68 * peso * PESO_TIPO[tipo] * fc

            for moneda, pm in MONEDAS:
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "localidad": "", "moneda": moneda, "sector": "",
                    "tipo_depositante": "",
                    "monto": round(monto_total * pm * float(_ruido()[0]), 2),
                    "numero_cuentas": max(1, int(monto_total * pm / 0.30 * float(_ruido()[0]))),
                    "fuente_endpoint": "captaciones_moneda",
                })
            for localidad, pl in PROVINCIAS:
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "localidad": localidad, "moneda": "", "sector": "",
                    "tipo_depositante": "",
                    "monto": round(monto_total * pl * float(_ruido()[0]), 2),
                    "numero_cuentas": max(1, int(monto_total * pl / 0.28 * float(_ruido()[0]))),
                    "fuente_endpoint": "captaciones_localidad",
                })
            for sector, ps in SECTORES_DEPOSITANTES:
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "localidad": "", "moneda": "", "sector": sector,
                    "tipo_depositante": sector,
                    "monto": round(monto_total * ps * float(_ruido()[0]), 2),
                    "numero_cuentas": max(1, int(monto_total * ps / 0.25 * float(_ruido()[0]))),
                    "fuente_endpoint": "captaciones_sector_depositante",
                })
    df = pd.DataFrame(rows)
    log.info("  captaciones: %s filas", f"{len(df):,}")
    return df


def generar_cartera(periodos):
    log.info("Generando cartera de créditos...")
    rows = []
    for periodo in periodos:
        fc  = factor_crecimiento(periodo)
        mora = morosidad_base(periodo)

        for nombre, tipo, peso in TODAS_ENTIDADES:
            saldo_total = ACTIVOS_BASE_2015 * 0.46 * peso * PESO_TIPO[tipo] * fc

            for clasif, pc in CLASIFICACIONES_RIESGO:
                # Distribución de riesgo correlacionada con mora
                factor_riesgo = 1 + (mora - 0.018) * 6 if clasif != "A - Normal" else 1.0
                saldo = saldo_total * pc * factor_riesgo * float(_ruido()[0])
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "clasificacion_riesgo": clasif, "genero": "", "localidad": "",
                    "moneda": "", "sector_economico": "", "tipo_cartera": "",
                    "saldo": round(saldo, 2),
                    "numero_deudores": max(1, int(saldo / 1.8 * float(_ruido()[0]))),
                    "fuente_endpoint": "cartera_clasificacion_riesgo",
                })
            for genero, pg in [("Masculino", 0.58), ("Femenino", 0.42)]:
                # Brecha de género se reduce progresivamente 2015→2025
                t = _t(periodo)
                brecha_f = min(0.72 + 0.003 * t, 1.0)
                factor_g = 1.0 if genero == "Masculino" else brecha_f
                saldo = saldo_total * pg * factor_g * float(_ruido()[0])
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "clasificacion_riesgo": "", "genero": genero, "localidad": "",
                    "moneda": "", "sector_economico": "", "tipo_cartera": "",
                    "saldo": round(saldo, 2),
                    "numero_deudores": max(1, int(saldo / 1.5 * float(_ruido()[0]))),
                    "fuente_endpoint": "cartera_genero",
                })
            for sector, ps in SECTORES_ECONOMICOS:
                # Turismo colapsa COVID y recupera
                f_sec = 1.0
                if sector == "Turismo y hotelería":
                    if date(2020, 3, 1) <= periodo <= date(2021, 6, 1):
                        f_sec = 0.45
                    elif date(2021, 7, 1) <= periodo <= date(2022, 6, 1):
                        f_sec = 0.70
                saldo = saldo_total * ps * f_sec * float(_ruido()[0])
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "clasificacion_riesgo": "", "genero": "", "localidad": "",
                    "moneda": "", "sector_economico": sector, "tipo_cartera": "",
                    "saldo": round(saldo, 2),
                    "numero_deudores": max(1, int(saldo / 2.0 * float(_ruido()[0]))),
                    "fuente_endpoint": "cartera_sectores_economicos",
                })
            for tipo_c, ptc in TIPOS_CARTERA:
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "clasificacion_riesgo": "", "genero": "", "localidad": "",
                    "moneda": "", "sector_economico": "", "tipo_cartera": tipo_c,
                    "saldo": round(saldo_total * ptc * float(_ruido()[0]), 2),
                    "numero_deudores": max(1, int(saldo_total * ptc / 1.7 * float(_ruido()[0]))),
                    "fuente_endpoint": "cartera_tipo",
                })
    df = pd.DataFrame(rows)
    log.info("  cartera_creditos: %s filas", f"{len(df):,}")
    return df


def generar_estados_financieros(periodos):
    log.info("Generando estados financieros...")
    rows = []
    EIC = [
        ("Cambio Express RD", "EIC", 0.25), ("Servicambio",     "EIC", 0.20),
        ("Cambio DM",         "EIC", 0.18), ("InterCambio RD",  "EIC", 0.15),
        ("Forex Dominicana",  "EIC", 0.12), ("Cambio Cibao",    "EIC", 0.10),
    ]
    for periodo in periodos:
        fc = factor_crecimiento(periodo)
        for nombre, tipo, peso in TODAS_ENTIDADES:
            activos = ACTIVOS_BASE_2015 * peso * PESO_TIPO[tipo] * fc
            for cuentas, tipo_ef in [(CUENTAS_SITUACION, "situacion"), (CUENTAS_RESULTADOS, "resultados")]:
                for cuenta, desc, ratio in cuentas:
                    rows.append({
                        "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                        "cuenta": cuenta, "descripcion": desc,
                        "monto": round(activos * ratio * float(_ruido(sigma=0.025)[0]), 2),
                        "tipo_estado": tipo_ef,
                    })
        for nombre, tipo, peso in EIC:
            activos = 15_000 * peso * fc * float(_ruido(sigma=0.03)[0])
            for cuentas, tipo_ef in [(CUENTAS_SITUACION, "situacion"), (CUENTAS_RESULTADOS, "resultados")]:
                for cuenta, desc, ratio in cuentas:
                    rows.append({
                        "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                        "cuenta": cuenta, "descripcion": desc,
                        "monto": round(activos * ratio * float(_ruido(sigma=0.03)[0]), 2),
                        "tipo_estado": tipo_ef,
                    })
    df = pd.DataFrame(rows)
    log.info("  estados_financieros: %s filas", f"{len(df):,}")
    return df


def generar_indicadores(periodos):
    log.info("Generando indicadores...")
    rows = []
    for periodo in periodos:
        t   = _t(periodo)
        mora = morosidad_base(periodo)
        # ROA/ROE caen en COVID, recuperan 2021+
        covid_roa = -0.004 if date(2020, 3, 1) <= periodo <= date(2021, 3, 1) else 0
        rec_roa   = min(0.003, 0.0002 * max(0, t - 66))   # t=66 → sep 2020

        for nombre, tipo, peso in TODAS_ENTIDADES:
            size_prem = 0.002 * (peso / 0.23)
            for ind_nom, ind_tipo, media, std in INDICADORES:
                if "Morosidad" in ind_nom or "Riesgo" in ind_nom:
                    valor = mora * (media / 0.018) + rng.normal(0, std * 0.3)
                elif ind_nom in ("ROA", "ROE"):
                    valor = media + covid_roa + rec_roa + size_prem + rng.normal(0, std * 0.4)
                elif "Liquidez" in ind_nom:
                    # Alta liquidez COVID (BCRD inyectó liquidez)
                    liq_covid = 0.04 if date(2020, 3, 1) <= periodo <= date(2021, 6, 1) else 0
                    valor = media + liq_covid + rng.normal(0, std * 0.4)
                else:
                    valor = media + rng.normal(0, std * 0.4)
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "tipo_indicador": ind_tipo, "nombre": ind_nom,
                    "valor": round(float(max(valor * 0.3, valor)), 6),
                    "fuente_endpoint": f"indicadores_{ind_tipo}",
                })
    df = pd.DataFrame(rows)
    log.info("  indicadores: %s filas", f"{len(df):,}")
    return df


def generar_solvencia(periodos):
    log.info("Generando solvencia...")
    rows = []
    for periodo in periodos:
        fc   = factor_crecimiento(periodo)
        mora = morosidad_base(periodo)
        # Solvencia inversamente correlacionada con mora, positiva con crecimiento PIB
        sol_base = 0.175 - (mora - 0.018) * 2.0 + rng.normal(0, 0.006)
        for nombre, tipo, peso in TODAS_ENTIDADES:
            activos = ACTIVOS_BASE_2015 * peso * PESO_TIPO[tipo] * fc
            apr     = activos * 0.67
            patrim  = activos * max(0.10, sol_base * 0.67)
            sol     = max(0.12, sol_base + rng.normal(0, 0.005))
            tier1   = sol * 0.80 + rng.normal(0, 0.003)
            tier2   = sol * 0.20 + rng.normal(0, 0.002)
            for comp, val in [
                ("Índice de Solvencia",          sol),
                ("Capital Primario (Tier 1)",    tier1),
                ("Capital Secundario (Tier 2)",  tier2),
                ("Activos Ponderados por Riesgo", apr),
                ("Patrimonio Técnico",            patrim),
            ]:
                rows.append({
                    "fecha": periodo, "entidad": nombre, "tipo_entidad": tipo,
                    "componente": comp, "valor": round(float(val), 4 if "Índice" in comp or "Capital" in comp else 2),
                })
    df = pd.DataFrame(rows)
    log.info("  solvencia: %s filas", f"{len(df):,}")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
#  CARGA A MYSQL / CSV
# ═══════════════════════════════════════════════════════════════════════════════

def _bulk_insert_chunks(engine, tabla_cls, records, chunk=5_000):
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(tabla_cls.__table__.delete())
    total = 0
    for i in range(0, len(records), chunk):
        with engine.begin() as conn:
            conn.execute(tabla_cls.__table__.insert(), records[i:i+chunk])
        total += len(records[i:i+chunk])
    return total


def cargar_a_mysql(dfs: dict) -> bool:
    try:
        from src.db.connection import create_database_if_not_exists, get_engine
        from src.db.models import (Captacion, CarteraCredito, EstadoFinanciero,
                                   Indicador, Solvencia, create_all_tables)
        log.info("Conectando a MySQL...")
        create_database_if_not_exists()
        engine = get_engine()
        create_all_tables(engine)
        now = datetime.utcnow()
        mapeo = {
            "captaciones":         (Captacion,          dfs["captaciones"]),
            "cartera_creditos":    (CarteraCredito,      dfs["cartera_creditos"]),
            "estados_financieros": (EstadoFinanciero,    dfs["estados_financieros"]),
            "indicadores":         (Indicador,           dfs["indicadores"]),
            "solvencia":           (Solvencia,           dfs["solvencia"]),
        }
        for nombre, (cls, df) in mapeo.items():
            if "cargado_en" in [c.name for c in cls.__table__.columns]:
                df = df.copy(); df["cargado_en"] = now
            n = _bulk_insert_chunks(engine, cls, df.to_dict(orient="records"))
            log.info("  ✓ %-28s %s filas", nombre, f"{n:,}")
        return True
    except Exception as e:
        log.warning("MySQL no disponible (%s). Solo CSV.", e)
        return False


def guardar_csv(dfs: dict):
    import pathlib
    out = pathlib.Path("data/processed")
    out.mkdir(parents=True, exist_ok=True)
    for nombre, df in dfs.items():
        ruta = out / f"{nombre}.csv"
        df.to_csv(ruta, index=False, encoding="utf-8-sig")
        log.info("  CSV: %s  (%s filas)", ruta, f"{len(df):,}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    log.info("=" * 65)
    log.info("  GENERADOR SIF-BANCARIO v2  —  2015-01 a 2025-12")
    log.info("  21 entidades · 132 meses · patrones macro RD reales")
    log.info("=" * 65)

    periodos = generar_periodos()
    log.info("Períodos: %d meses", len(periodos))

    dfs = {
        "captaciones":         generar_captaciones(periodos),
        "cartera_creditos":    generar_cartera(periodos),
        "estados_financieros": generar_estados_financieros(periodos),
        "indicadores":         generar_indicadores(periodos),
        "solvencia":           generar_solvencia(periodos),
    }

    total = sum(len(d) for d in dfs.values())
    log.info("─" * 65)
    log.info("TOTAL: %s filas", f"{total:,}")
    for k, v in dfs.items():
        log.info("  %-28s %s", k, f"{len(v):,}")
    log.info("─" * 65)

    guardar_csv(dfs)
    ok = cargar_a_mysql(dfs)
    log.info("=" * 65)
    log.info("  DONE — datos en data/processed/*.csv%s",
             " y MySQL" if ok else " (MySQL no disponible)")
    log.info("=" * 65)


if __name__ == "__main__":
    main()
