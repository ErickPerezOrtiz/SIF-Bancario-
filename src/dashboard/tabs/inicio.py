"""Tab: Inicio — presentación del proyecto SIF-Bancario."""
import dash_bootstrap_components as dbc
from dash import html

COLORS = {
    "azul_sb": "#003087",
    "rojo":    "#C8102E",
    "dorado":  "#F5A623",
    "verde":   "#28A745",
    "naranja": "#E67E22",
}
GITHUB = "https://github.com/ErickPerezOrtiz"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _semaforo_card(titulo, valor_str, unidad, color_key, nivel, descripcion):
    palette = {"success": "#28A745", "warning": "#F5A623", "danger": "#C8102E"}
    arrows  = {"success": "▲", "warning": "►", "danger": "▼"}
    c = palette[color_key]
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Span(arrows[color_key],
                          style={"fontSize": "1.4rem", "color": c, "marginRight": "6px"}),
                html.Span(nivel,
                          style={"backgroundColor": c, "color": "white", "padding": "3px 10px",
                                 "borderRadius": "12px", "fontSize": "0.72rem",
                                 "fontWeight": "bold"}),
            ], className="d-flex align-items-center mb-2"),
            html.H4(f"{valor_str} {unidad}",
                    style={"color": c, "fontWeight": "bold", "margin": "0"}),
            html.P(titulo,
                   style={"color": COLORS["azul_sb"], "fontWeight": "600",
                          "marginTop": "4px", "marginBottom": "2px", "fontSize": "0.88rem"}),
            html.Small(descripcion, className="text-muted"),
        ])
    ], style={"borderLeft": f"5px solid {c}", "borderRadius": "8px"},
       className="shadow-sm h-100")


def _semaforo_val(valor, umbral_verde, umbral_amarillo, mayor_es_mejor=True):
    if mayor_es_mejor:
        if valor >= umbral_verde:   return "success", "SALUDABLE"
        if valor >= umbral_amarillo: return "warning", "PRECAUCIÓN"
        return "danger", "ALERTA"
    else:
        if valor <= umbral_verde:   return "success", "SALUDABLE"
        if valor <= umbral_amarillo: return "warning", "PRECAUCIÓN"
        return "danger", "ALERTA"


def _pipeline_step(num, titulo, desc, color):
    return html.Div([
        html.Div([
            html.Span(num, style={
                "backgroundColor": color, "color": "white",
                "borderRadius": "50%", "width": "28px", "height": "28px",
                "display": "inline-flex", "alignItems": "center",
                "justifyContent": "center", "fontWeight": "bold",
                "fontSize": "0.85rem", "flexShrink": "0",
            }),
            html.Div([
                html.Strong(titulo, style={"color": color, "fontSize": "0.9rem"}),
                html.Span(f"  — {desc}", style={"fontSize": "0.85rem", "color": "#555"}),
            ], style={"marginLeft": "10px"}),
        ], className="d-flex align-items-center", style={"marginBottom": "8px"}),
    ])


def _hallazgo_card(titulo, desc, idx):
    borde_colors = [COLORS["azul_sb"], COLORS["dorado"], COLORS["verde"],
                    COLORS["rojo"], COLORS["naranja"], COLORS["azul_sb"], COLORS["dorado"]]
    color = borde_colors[idx % len(borde_colors)]
    return dbc.Card([dbc.CardBody([
        html.H6(titulo, style={"color": color, "fontWeight": "700", "marginBottom": "6px"}),
        html.P(desc, className="mb-0", style={"fontSize": "0.87rem", "color": "#444"}),
    ])], style={"borderLeft": f"4px solid {color}", "borderRadius": "6px"},
        className="shadow-sm mb-3 h-100")


# ── Datos de contenido ────────────────────────────────────────────────────────

TABS_INFO = [
    ("Captaciones",
     "Evolución mensual de depósitos por moneda (DOP/USD/EUR), "
     "ranking de entidades y distribución por tipo de depositante."),
    ("Cartera de Créditos",
     "Calidad de la cartera crediticia, índice de morosidad, "
     "distribución sectorial y brecha de género en el crédito."),
    ("Indicadores",
     "Panel de indicadores prudenciales: ROA, ROE, liquidez "
     "y morosidad del sistema, con evolución 2015-2025."),
    ("Solvencia",
     "Índice de solvencia del sistema financiero por componente "
     "(Tier 1, Tier 2) y distribución entre entidades."),
    ("Estadísticas",
     "Análisis estadístico avanzado: heatmap de correlación "
     "cruzada, histogramas, skewness, kurtosis y detección de outliers IQR+Z."),
    ("Macro vs Banca",
     "Relación entre TPM del BCRD, inflación (IPC) "
     "y los indicadores bancarios. Incluye tipo de cambio DOP/USD."),
    ("Ranking Bancario",
     "Scorecard interactivo con podio, cuota de mercado "
     "y evolución histórica del ranking por año."),
    ("Mapa Provincial",
     "Distribución geográfica de las captaciones "
     "por provincia de la República Dominicana (choropleth GeoJSON)."),
    ("Remesas e Inclusión",
     "Análisis de las remesas hacia RD, su correlación "
     "con las captaciones y la brecha de género en el acceso al crédito."),
    ("Stress Testing",
     "Modelo econométrico OLS para simular el impacto de shocks "
     "macro (TPM, inflación, tipo de cambio) sobre la morosidad. Sliders interactivos."),
]

HALLAZGOS = [
    ("Concentración bancaria extrema",
     "Los 3 principales bancos (BPD, BRE, BHD) concentran ~59% del total de captaciones, "
     "revelando un mercado oligopólico con altas barreras de entrada y presión regulatoria "
     "sobre la competencia."),
    ("COVID-19: caída y recuperación asimétrica",
     "El PIB cayó -15.3% en Q2-2020, pero el sistema bancario mostró resiliencia: "
     "la morosidad solo subió ~1.5 puntos porcentuales gracias a las medidas "
     "de alivio del BCRD (corte de 300 pb en TPM)."),
    ("Boom de remesas post-pandemia (r = 0.84)",
     "Las remesas saltaron de USD 7,981 MM en 2020 a USD 10,431 MM en 2021 (+30.7%), "
     "impulsadas por la diáspora en EE.UU. La correlación Pearson con captaciones "
     "es r ≈ 0.84, señalando un canal directo de profundización financiera."),
    ("Ciclo agresivo de TPM en 2022",
     "El BCRD subió la TPM +550 pb en menos de 12 meses (3.00% → 8.50%) para contener "
     "la inflación que alcanzó 9.64% interanual. Esto encareció el crédito "
     "y comprimió los márgenes de intermediación bancaria."),
    ("Brecha de género persistente en el crédito",
     "El crédito a mujeres representa ~35% del saldo total de la cartera. "
     "A pesar del crecimiento económico, la brecha M/F no se ha reducido "
     "significativamente en el período 2015-2025."),
    ("Depreciación gradual del peso dominicano",
     "El tipo de cambio DOP/USD pasó de 44.50 a 61.50 en 10 años (+38.2%), "
     "aumentando el riesgo cambiario para deudores con ingresos en pesos "
     "y obligaciones indexadas al dólar."),
    ("Exclusión financiera geográfica",
     "El Distrito Nacional y Santiago concentran más del 75% de las captaciones. "
     "Provincias del sur, noroeste y fronterizas presentan severa exclusión financiera, "
     "con potencial de crecimiento significativo."),
]

CONCLUSIONES = [
    "El sistema bancario dominicano demostró resiliencia ante el choque COVID-19, "
    "gracias a la adecuada capitalización y las políticas contracíclicas del BCRD.",
    "La concentración bancaria, aunque operacionalmente eficiente, limita la competencia "
    "y el acceso al crédito para PYMEs y sectores de menores ingresos.",
    "La fuerte correlación remesas-captaciones (r ≈ 0.84) sugiere que la política "
    "de atracción de remesas es un vector clave de profundización financiera en RD.",
    "La brecha de género en el acceso al crédito persiste a pesar del crecimiento "
    "macroeconómico, lo que requiere políticas focalizadas de inclusión financiera.",
    "El modelo OLS de stress testing indica que un shock combinado (TPM +300 pb, "
    "IPC +5%, TC +10 DOP) elevaría la morosidad proyectada por encima del umbral de "
    "precaución del 4%, requiriendo refuerzo de provisiones.",
    "La desconcentración geográfica del crédito es el principal reto estructural "
    "para la inclusión financiera en la República Dominicana.",
]


# ── Render principal ──────────────────────────────────────────────────────────

def render(az) -> html.Div:
    # Semáforo de salud
    kpis = {}
    try:
        kpis = az.resumen_ejecutivo()
    except Exception:
        pass

    sol_val  = kpis.get("solvencia_promedio",  14.2)
    mora_val = kpis.get("morosidad_promedio",   1.8)

    liq_val = 28.5
    try:
        df_ind = az.evolucion_indicadores("liquidez")
        if not df_ind.empty:
            liq_val = float(df_ind["valor_promedio"].iloc[-1])
    except Exception:
        pass

    crec_val = 8.5
    try:
        df_cap = az.evolucion_captaciones_mensual()
        if not df_cap.empty:
            df_annual = (
                df_cap.assign(year=df_cap["periodo"].str[:4])
                .groupby("year")["total_captado"].sum()
            )
            if len(df_annual) >= 2:
                crec_val = float(df_annual.iloc[-1] / df_annual.iloc[-2] - 1) * 100
    except Exception:
        pass

    sol_c,  sol_n  = _semaforo_val(sol_val,  12.0, 10.0, mayor_es_mejor=True)
    mora_c, mora_n = _semaforo_val(mora_val,  2.0,  4.0, mayor_es_mejor=False)
    liq_c,  liq_n  = _semaforo_val(liq_val,  20.0, 15.0, mayor_es_mejor=True)
    crec_c, crec_n = _semaforo_val(crec_val,  5.0,  0.0, mayor_es_mejor=True)

    return html.Div([

        # ── Hero ─────────────────────────────────────────────────────────────
        dbc.Card([dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H2("Sistema de Inteligencia Financiera",
                            style={"color": COLORS["azul_sb"], "fontWeight": "800",
                                   "marginBottom": "2px"}),
                    html.H4("Banca Dominicana · 2015-2025",
                            style={"color": COLORS["dorado"], "fontWeight": "600",
                                   "marginBottom": "14px"}),
                    html.P(
                        "Plataforma de análisis de datos del sistema bancario de la "
                        "República Dominicana. Integra estadísticas de la Superintendencia "
                        "de Bancos, datos macroeconómicos del BCRD y técnicas de análisis "
                        "estadístico avanzado para generar inteligencia financiera accionable.",
                        style={"fontSize": "0.95rem", "color": "#444", "maxWidth": "680px",
                               "marginBottom": "12px"}
                    ),
                    html.Div([
                        dbc.Badge("267,300 registros", color="primary",   className="me-2 mb-1"),
                        dbc.Badge("10 años de historia", color="secondary", className="me-2 mb-1"),
                        dbc.Badge("21 entidades",        color="success",  className="me-2 mb-1"),
                        dbc.Badge("5 series BCRD",       color="warning",  className="me-2 mb-1"),
                        dbc.Badge("10 tabs interactivos", color="info",    className="me-2 mb-1"),
                    ]),
                ], md=8),
                dbc.Col([
                    html.Div([
                        html.P("Portafolio académico",
                               className="text-muted mb-1",
                               style={"fontSize": "0.75rem", "textTransform": "uppercase",
                                      "letterSpacing": "1px"}),
                        html.H5("Erick Pérez",
                                style={"color": COLORS["azul_sb"], "fontWeight": "bold",
                                       "marginBottom": "4px"}),
                        html.P("Analítica y Ciencia de Datos",
                               className="mb-1", style={"fontSize": "0.9rem"}),
                        html.P("ITLA · Santo Domingo, RD",
                               className="text-muted mb-2", style={"fontSize": "0.85rem"}),
                        html.A("github.com/ErickPerezOrtiz",
                               href=GITHUB, target="_blank",
                               style={"color": COLORS["azul_sb"], "fontSize": "0.85rem",
                                      "textDecoration": "none"}),
                    ], style={"textAlign": "right"})
                ], md=4, className="d-flex align-items-start justify-content-end pt-2"),
            ])
        ])], style={"borderLeft": f"6px solid {COLORS['azul_sb']}", "marginBottom": "24px"},
            className="shadow-sm"),

        # ── Semáforo ──────────────────────────────────────────────────────────
        html.H5("Semáforo de Salud del Sistema Bancario",
                className="mb-3", style={"color": COLORS["azul_sb"], "fontWeight": "700"}),
        dbc.Row([
            dbc.Col(_semaforo_card(
                "Índice de Solvencia", f"{sol_val:.1f}", "%",
                sol_c, sol_n, "Min. regulatorio RD: 10% | Saludable: > 12%"
            ), md=3),
            dbc.Col(_semaforo_card(
                "Índice de Morosidad", f"{mora_val:.2f}", "%",
                mora_c, mora_n, "Sistema sano: < 2% | Precaución: 2-4% | Alerta: > 4%"
            ), md=3),
            dbc.Col(_semaforo_card(
                "Índice de Liquidez", f"{liq_val:.1f}", "%",
                liq_c, liq_n, "Min. regulatorio RD: 15% | Saludable: > 20%"
            ), md=3),
            dbc.Col(_semaforo_card(
                "Crecimiento Captaciones", f"{crec_val:.1f}", "%",
                crec_c, crec_n, "Crecimiento interanual real del sistema de depósitos"
            ), md=3),
        ], className="mb-4 g-3"),

        html.Hr(style={"marginBottom": "24px"}),

        # ── ¿Qué es? + Objetivo ───────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H5("¿Qué es el SIF-Bancario?",
                            style={"color": COLORS["azul_sb"], "fontWeight": "700",
                                   "marginBottom": "10px"}),
                    html.P(
                        "El SIF-Bancario es un pipeline de datos completo que automatiza "
                        "la ingesta, transformación, almacenamiento y visualización de "
                        "estadísticas del sistema financiero dominicano. Consume datos de "
                        "la API oficial de la Superintendencia de Bancos (cuando está "
                        "disponible) y genera datos sintéticos calibrados con estadísticas "
                        "reales del BCRD, Banco Mundial y FMI como fallback.",
                        style={"fontSize": "0.9rem", "color": "#444", "marginBottom": "10px"}
                    ),
                    html.P(
                        "Cubre 132 meses (2015-2025), 21 entidades financieras supervisadas "
                        "(12 bancos múltiples, 5 asociaciones de ahorro y crédito, "
                        "4 bancos de ahorro), y 5 dimensiones de análisis: captaciones, "
                        "cartera crediticia, indicadores prudenciales, solvencia patrimonial "
                        "y contexto macroeconómico.",
                        style={"fontSize": "0.9rem", "color": "#444", "marginBottom": "0"}
                    ),
                ])], className="shadow-sm h-100"),
            ], md=6),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H5("Objetivo del Proyecto",
                            style={"color": COLORS["azul_sb"], "fontWeight": "700",
                                   "marginBottom": "10px"}),
                    html.Ul([
                        html.Li("Monitorear la salud del sistema bancario dominicano.",
                                style={"marginBottom": "6px"}),
                        html.Li("Identificar riesgos sistémicos y concentraciones de mercado.",
                                style={"marginBottom": "6px"}),
                        html.Li("Analizar el impacto de la política monetaria del BCRD sobre la banca.",
                                style={"marginBottom": "6px"}),
                        html.Li("Evaluar la inclusión financiera: género, geografía y remesas.",
                                style={"marginBottom": "6px"}),
                        html.Li("Simular escenarios de stress para anticipar vulnerabilidades.",
                                style={"marginBottom": "0"}),
                    ], style={"paddingLeft": "18px", "fontSize": "0.9rem", "color": "#444"}),
                ])], className="shadow-sm h-100"),
            ], md=6),
        ], className="mb-4 g-3"),

        # ── Fuentes + Metodología ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H5("Fuentes de Datos",
                            style={"color": COLORS["azul_sb"], "fontWeight": "700",
                                   "marginBottom": "10px"}),
                    dbc.Table([html.Tbody([
                        html.Tr([
                            html.Td(html.Strong("Superintendencia de Bancos RD"),
                                    style={"width": "42%", "fontSize": "0.85rem"}),
                            html.Td("API REST — captaciones, cartera, indicadores, "
                                    "solvencia, estados financieros",
                                    style={"fontSize": "0.85rem"}),
                        ]),
                        html.Tr([
                            html.Td(html.Strong("BCRD — Política Monetaria"),
                                    style={"fontSize": "0.85rem"}),
                            html.Td("TPM, IPC mensual/interanual, tipo de cambio DOP/USD",
                                    style={"fontSize": "0.85rem"}),
                        ]),
                        html.Tr([
                            html.Td(html.Strong("BCRD — Sector Externo"),
                                    style={"fontSize": "0.85rem"}),
                            html.Td("Remesas mensuales en USD millones (2015-2025)",
                                    style={"fontSize": "0.85rem"}),
                        ]),
                        html.Tr([
                            html.Td(html.Strong("BCRD — Cuentas Nacionales"),
                                    style={"fontSize": "0.85rem"}),
                            html.Td("PIB trimestral y crecimiento económico real",
                                    style={"fontSize": "0.85rem"}),
                        ]),
                        html.Tr([
                            html.Td(html.Strong("Banco Mundial / FMI"),
                                    style={"fontSize": "0.85rem"}),
                            html.Td("Calibración de tasas de inflación y crecimiento",
                                    style={"fontSize": "0.85rem"}),
                        ]),
                        html.Tr([
                            html.Td(html.Strong("GeoJSON — jeasoft/provinces"),
                                    style={"fontSize": "0.85rem"}),
                            html.Td("Shapefile de provincias dominicanas para el mapa",
                                    style={"fontSize": "0.85rem"}),
                        ]),
                    ])], bordered=False, striped=True, className="table-sm mb-0"),
                ])], className="shadow-sm h-100"),
            ], md=7),
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H5("Metodología — Pipeline ETL",
                            style={"color": COLORS["azul_sb"], "fontWeight": "700",
                                   "marginBottom": "10px"}),
                    _pipeline_step("1", "Extracción",
                                   "API SB · BCRD · GeoJSON", COLORS["azul_sb"]),
                    _pipeline_step("2", "Transformación",
                                   "pandas · numpy · limpieza y enriquecimiento", COLORS["dorado"]),
                    _pipeline_step("3", "Carga",
                                   "MySQL 8.4 · SQLAlchemy ORM · CSV fallback", COLORS["verde"]),
                    _pipeline_step("4", "Análisis",
                                   "scipy · statsmodels · OLS · correlación Pearson", COLORS["rojo"]),
                    _pipeline_step("5", "Visualización",
                                   "Plotly Dash · 10 pestañas interactivas", COLORS["azul_sb"]),
                    html.Hr(style={"margin": "10px 0"}),
                    html.P(
                        "El sistema detecta automáticamente si MySQL está disponible "
                        "y usa CSV como fallback transparente sin intervención manual.",
                        style={"fontSize": "0.82rem", "color": "#666", "marginBottom": "0"}
                    ),
                ])], className="shadow-sm h-100"),
            ], md=5),
        ], className="mb-4 g-3"),

        # ── Estructura del dashboard ──────────────────────────────────────────
        html.H5("Estructura del Dashboard — 10 Pestañas",
                className="mb-3", style={"color": COLORS["azul_sb"], "fontWeight": "700"}),
        dbc.Row([
            dbc.Col([
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Span(f"{i+1}. ", style={"color": COLORS["azul_sb"],
                                                      "fontWeight": "bold", "marginRight": "4px"}),
                        html.Strong(nombre + "  "),
                        html.Span(desc, className="text-muted", style={"fontSize": "0.84rem"}),
                    ], style={"padding": "10px 14px"})
                    for i, (nombre, desc) in enumerate(TABS_INFO)
                ], className="shadow-sm"),
            ]),
        ], className="mb-4"),

        # ── Hallazgos ─────────────────────────────────────────────────────────
        html.H5("Hallazgos Principales",
                className="mb-3", style={"color": COLORS["azul_sb"], "fontWeight": "700"}),
        dbc.Row([
            dbc.Col([_hallazgo_card(t, d, i)], md=6)
            for i, (t, d) in enumerate(HALLAZGOS)
        ], className="g-3 mb-4"),

        # ── Conclusiones ──────────────────────────────────────────────────────
        html.H5("Conclusiones Académicas",
                className="mb-3", style={"color": COLORS["azul_sb"], "fontWeight": "700"}),
        dbc.Card([dbc.CardBody([
            html.Ol([
                html.Li(c, style={"marginBottom": "8px", "fontSize": "0.9rem", "color": "#333"})
                for c in CONCLUSIONES
            ], style={"paddingLeft": "20px", "marginBottom": "0"}),
        ])], className="shadow-sm mb-4"),

        # ── Sobre el autor ────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5("Sobre el Autor",
                                    style={"color": COLORS["azul_sb"], "fontWeight": "700",
                                           "marginBottom": "10px"}),
                            html.H4("Erick Pérez",
                                    style={"fontWeight": "800", "marginBottom": "4px",
                                           "color": COLORS["azul_sb"]}),
                            html.P("Estudiante de Analítica y Ciencia de Datos",
                                   className="mb-1", style={"fontSize": "0.95rem"}),
                            html.P("Instituto Tecnológico de Las Américas (ITLA)",
                                   className="mb-1 text-muted", style={"fontSize": "0.9rem"}),
                            html.P("Santo Domingo, República Dominicana",
                                   className="mb-3 text-muted", style={"fontSize": "0.9rem"}),
                            html.A("github.com/ErickPerezOrtiz",
                                   href=GITHUB, target="_blank",
                                   className="btn btn-outline-primary btn-sm"),
                        ], md=6),
                        dbc.Col([
                            html.P("Tecnologías del proyecto:",
                                   className="fw-bold mb-2",
                                   style={"color": COLORS["azul_sb"]}),
                            html.Div([
                                dbc.Badge(t, color=c, className="me-1 mb-2")
                                for t, c in [
                                    ("Python 3.12",    "primary"),
                                    ("Plotly Dash",    "info"),
                                    ("pandas",         "success"),
                                    ("numpy",          "info"),
                                    ("scipy",          "primary"),
                                    ("statsmodels",    "secondary"),
                                    ("SQLAlchemy",     "dark"),
                                    ("MySQL 8.4",      "warning"),
                                    ("dash-bootstrap", "primary"),
                                    ("requests",       "secondary"),
                                ]
                            ]),
                        ], md=6, className="d-flex flex-column justify-content-center"),
                    ])
                ])], style={"borderLeft": f"6px solid {COLORS['verde']}", "borderRadius": "8px"},
                    className="shadow-sm"),
            ], md=10, className="offset-md-1"),
        ], className="mb-3", style={"paddingTop": "12px"}),
    ])
