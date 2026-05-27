"""Dashboard interactivo — Sistema de Inteligencia Financiera Banca Dominicana."""
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

from src.analysis.statistics import FinancialAnalyzer
from config.settings import DASH_HOST, DASH_PORT, DASH_DEBUG
from src.dashboard.tabs import macro_banca, ranking, mapa, remesas, stress, inicio, conceptos

logger = logging.getLogger(__name__)

COLORS = {
    "azul_sb": "#003087",
    "rojo":    "#C8102E",
    "dorado":  "#F5A623",
    "gris":    "#6C757D",
    "verde":   "#28A745",
    "bg":      "#F8F9FA",
    "card_bg": "#FFFFFF",
}

COVID_P0, COVID_P1 = "2020-03", "2020-12"   # period-string format

ANALYZER = None


def get_analyzer() -> FinancialAnalyzer:
    global ANALYZER
    if ANALYZER is None:
        ANALYZER = FinancialAnalyzer()
    return ANALYZER


# ── Helpers ───────────────────────────────────────────────────────────────────

def _kpi_card(titulo: str, valor: str, subtitulo: str, color: str) -> dbc.Card:
    return dbc.Card([
        dbc.CardBody([
            html.H6(titulo, className="text-muted mb-1", style={"fontSize": "0.8rem"}),
            html.H3(valor, style={"color": color, "fontWeight": "bold"}),
            html.Small(subtitulo, className="text-muted"),
        ])
    ], className="shadow-sm border-0 h-100")


def _info_card(titulo: str, parrafos: list) -> dbc.Card:
    """Panel informativo azul claro consistente en todos los tabs."""
    return dbc.Card([dbc.CardBody([
        html.H6(titulo,
                style={"color": COLORS["azul_sb"], "fontWeight": "700",
                       "marginBottom": "8px"}),
        *[html.P(p, className="mb-1" if i < len(parrafos)-1 else "mb-0",
                 style={"fontSize": "0.87rem", "color": "#444"})
          for i, p in enumerate(parrafos)],
    ])], style={
        "backgroundColor": "#EBF3FB",
        "borderLeft": f"4px solid {COLORS['azul_sb']}",
        "borderRadius": "6px",
        "border": "1px solid #D0E4F5",
    }, className="mb-3")


def _add_covid_band(fig, x0=COVID_P0, x1=COVID_P1):
    """Banda sombreada gris para el período COVID (2020-03 a 2020-12)."""
    fig.add_vrect(
        x0=x0, x1=x1,
        fillcolor="gray", opacity=0.12, line_width=0,
        annotation_text="COVID-19",
        annotation_position="top left",
        annotation_font_size=10,
        annotation_font_color="gray",
    )
    return fig


# ── Layout ────────────────────────────────────────────────────────────────────

def _fmt_millones(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if v >= 1_000_000:
        return f"RD$ {v/1_000_000:.2f} billones"
    if v >= 1_000:
        return f"RD$ {v/1_000:.1f} mil MM"
    return f"RD$ {v:,.0f} MM"


def _kpi_row_placeholder() -> dbc.Row:
    """Fila de KPIs con valores 'Cargando…' mostrada al arrancar."""
    specs = [
        ("Total Captado (DOP)",      "Cargando…", "Depósitos del público",              COLORS["azul_sb"]),
        ("Cartera de Créditos",      "Cargando…", "Saldo total prestado",               COLORS["rojo"]),
        ("Entidades Supervisadas",   "Cargando…", "Bancos, asociaciones y financieras", COLORS["dorado"]),
        ("Períodos Disponibles",     "Cargando…", "Meses de histórico",                 COLORS["verde"]),
    ]
    return dbc.Row(
        [dbc.Col(_kpi_card(t, v, s, c), md=3) for t, v, s, c in specs],
        className="mb-4 g-3",
    )


def build_layout() -> html.Div:
    return html.Div([
        # ── Navbar ──
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand(
                    "SIF — Banca Dominicana",
                    style={"color": "white", "fontWeight": "700", "fontSize": "1.1rem"}
                ),
                html.Span(
                    "Superintendencia de Bancos · RD",
                    style={"color": "rgba(255,255,255,0.7)", "fontSize": "0.85rem",
                           "marginLeft": "auto"}
                ),
            ]),
            color=COLORS["azul_sb"], dark=True, className="mb-4 shadow"
        ),

        dbc.Container([
            # ── KPI Cards (lazy) ──
            dcc.Interval(id="kpi-trigger", interval=800, n_intervals=0, max_intervals=1),
            html.Div(id="kpi-row", children=_kpi_row_placeholder()),

            # ── Tabs ──
            dbc.Tabs([
                dbc.Tab(label="Inicio",              tab_id="tab-inicio"),
                dbc.Tab(label="Conceptos",           tab_id="tab-conceptos"),
                dbc.Tab(label="Captaciones",         tab_id="tab-captaciones"),
                dbc.Tab(label="Cartera de Créditos", tab_id="tab-cartera"),
                dbc.Tab(label="Indicadores",         tab_id="tab-indicadores"),
                dbc.Tab(label="Solvencia",           tab_id="tab-solvencia"),
                dbc.Tab(label="Estadísticas",        tab_id="tab-stats"),
                dbc.Tab(label="Macro vs Banca",      tab_id="tab-macro"),
                dbc.Tab(label="Ranking Bancario",    tab_id="tab-ranking"),
                dbc.Tab(label="Mapa Provincial",     tab_id="tab-mapa"),
                dbc.Tab(label="Remesas e Inclusión", tab_id="tab-remesas"),
                dbc.Tab(label="Stress Testing",      tab_id="tab-stress"),
            ], id="tabs-main", active_tab="tab-inicio", className="mb-4"),

            html.Div(id="tab-content"),

            # ── Footer ──
            html.Hr(),
            html.P([
                "Portafolio de ",
                html.Strong("Erick Pérez"),
                " · Analítica y Ciencia de Datos · ITLA, Santo Domingo RD · ",
                html.A("github.com/ErickPerezOrtiz",
                       href="https://github.com/ErickPerezOrtiz", target="_blank"),
                " · Datos: ",
                html.A("desarrollador.sb.gob.do",
                       href="https://desarrollador.sb.gob.do", target="_blank"),
            ], className="text-center text-muted small pb-3"),
        ], fluid=True),
    ], style={"backgroundColor": COLORS["bg"], "minHeight": "100vh"})


# ── Callbacks ─────────────────────────────────────────────────────────────────

def register_callbacks(app: dash.Dash):

    @app.callback(
        Output("kpi-row", "children"),
        Input("kpi-trigger", "n_intervals"),
        prevent_initial_call=True,
    )
    def load_kpis(_):
        az = get_analyzer()
        kpis = {}
        try:
            kpis = az.resumen_ejecutivo()
        except Exception as e:
            logger.warning("KPIs fallaron: %s", e)
        specs = [
            ("Total Captado (DOP)",    _fmt_millones(kpis.get("total_captado_DOP", 0)),
             "Depósitos del público",              COLORS["azul_sb"]),
            ("Cartera de Créditos",    _fmt_millones(kpis.get("total_cartera_DOP", 0)),
             "Saldo total prestado",               COLORS["rojo"]),
            ("Entidades Supervisadas", str(kpis.get("entidades_unicas", "—")),
             "Bancos, asociaciones y financieras", COLORS["dorado"]),
            ("Períodos Disponibles",   str(kpis.get("periodos_disponibles", "—")),
             "Meses de histórico",                 COLORS["verde"]),
        ]
        return dbc.Row(
            [dbc.Col(_kpi_card(t, v, s, c), md=3) for t, v, s, c in specs],
            className="mb-4 g-3",
        )

    @app.callback(Output("tab-content", "children"), Input("tabs-main", "active_tab"))
    def render_tab(tab):
        az = get_analyzer()

        # ── Inicio ────────────────────────────────────────────────────────────
        if tab == "tab-inicio":
            try:
                return inicio.render(az)
            except Exception as e:
                return dbc.Alert(f"Error en tab Inicio: {e}", color="danger")

        # ── Conceptos ─────────────────────────────────────────────────────────
        elif tab == "tab-conceptos":
            try:
                return conceptos.render()
            except Exception as e:
                return dbc.Alert(f"Error en tab Conceptos: {e}", color="danger")

        # ── Captaciones ───────────────────────────────────────────────────────
        if tab == "tab-captaciones":
            df_evol = az.evolucion_captaciones_mensual()
            df_top  = az.top_entidades_captaciones(10)
            df_dep  = az.distribucion_sector_depositante()

            fig_evol = px.line(
                df_evol, x="periodo", y="total_captado", color="moneda",
                title="Evolución de Captaciones por Moneda",
                labels={"total_captado": "Monto (RD$)", "periodo": "Período"},
                color_discrete_sequence=[COLORS["azul_sb"], COLORS["dorado"], COLORS["verde"]]
            )
            fig_evol.update_layout(plot_bgcolor="white", paper_bgcolor="white")
            _add_covid_band(fig_evol)

            fig_top = px.bar(
                df_top, x="total_captado", y="entidad", orientation="h",
                title="Top 10 Entidades por Captaciones",
                labels={"total_captado": "Total Captado (RD$)", "entidad": "Entidad"},
                color="total_captado", color_continuous_scale="Blues"
            )
            fig_top.update_layout(yaxis={"categoryorder": "total ascending"},
                                  plot_bgcolor="white", paper_bgcolor="white")

            fig_dep = px.pie(
                df_dep, values="total_captado", names="tipo_depositante",
                title="Distribución por Tipo de Depositante",
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            # Calcular share de los 3 principales
            share_top3 = 0.0
            if not df_top.empty:
                share_top3 = df_top.head(3)["total_captado"].sum() / df_top["total_captado"].sum() * 100

            return html.Div([
                _info_card(
                    "¿Qué son las captaciones y cómo interpretarlas?",
                    [
                        [html.Strong("¿Qué son las captaciones? "),
                         "Son los depósitos que el público (personas, empresas, gobierno) "
                         "hace en el sistema bancario. Incluyen cuentas corrientes, de ahorro "
                         "y depósitos a plazo. Son la principal fuente de fondeo de los bancos "
                         "para otorgar créditos."],
                        [html.Strong("¿Qué representan DOP y USD? "),
                         "DOP (peso dominicano) son los depósitos en moneda local —la mayoría— "
                         "y USD (dólar) los depósitos en moneda extranjera, típicamente de "
                         "empresas exportadoras o importadoras. Una alta dolarización (> 30%) "
                         "puede indicar desconfianza en la moneda local."],
                        [html.Strong("Hallazgo principal: "),
                         f"Los 3 principales bancos concentran el {share_top3:.1f}% de las "
                         "captaciones, revelando un mercado altamente concentrado con "
                         "implicaciones para la competencia y las tasas de interés pasivas "
                         "que reciben los ahorrantes."],
                    ]
                ),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_evol), md=12, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_top),  md=7,  className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_dep),  md=5,  className="mb-3"),
                ]),
            ])

        # ── Cartera de Créditos ───────────────────────────────────────────────
        elif tab == "tab-cartera":
            df_cal    = az.calidad_cartera()
            df_sector = az.cartera_por_sector()
            df_genero = az.brecha_genero_credito()

            fig_cal = go.Figure()
            if not df_cal.empty:
                fig_cal.add_trace(go.Scatter(
                    x=df_cal["periodo"], y=df_cal["cartera_normal"],
                    name="Cartera Normal", fill="tozeroy",
                    line={"color": COLORS["verde"]}
                ))
                fig_cal.add_trace(go.Scatter(
                    x=df_cal["periodo"], y=df_cal["cartera_riesgo"],
                    name="Cartera en Riesgo", fill="tozeroy",
                    line={"color": COLORS["rojo"]}
                ))
                fig_cal.add_trace(go.Scatter(
                    x=df_cal["periodo"], y=df_cal["indice_morosidad"],
                    name="Índice Morosidad (%)", yaxis="y2",
                    line={"color": COLORS["dorado"], "dash": "dash"}
                ))
                fig_cal.update_layout(
                    title="Calidad de Cartera e Índice de Morosidad",
                    yaxis2={"overlaying": "y", "side": "right", "ticksuffix": "%"},
                    plot_bgcolor="white", paper_bgcolor="white"
                )
            _add_covid_band(fig_cal)

            fig_sector = px.treemap(
                df_sector, path=["sector_economico"], values="total_saldo",
                title="Cartera por Sector Económico",
                color="total_saldo", color_continuous_scale="RdBu_r"
            )

            fig_gen = px.bar(
                df_genero, x="periodo", y="saldo_total", color="genero",
                barmode="group", title="Brecha de Género en Acceso al Crédito",
                labels={"saldo_total": "Saldo (RD$)", "periodo": "Período"},
                color_discrete_map={
                    "M": COLORS["azul_sb"], "F": COLORS["rojo"],
                    "Masculino": COLORS["azul_sb"], "Femenino": COLORS["rojo"],
                }
            )
            fig_gen.update_layout(plot_bgcolor="white", paper_bgcolor="white")

            # Morosidad último período
            mora_actual = ""
            if not df_cal.empty:
                mora_actual = f"{df_cal['indice_morosidad'].iloc[-1]:.2f}%"

            return html.Div([
                _info_card(
                    "¿Qué es la cartera de créditos y cómo interpretarla?",
                    [
                        [html.Strong("¿Qué es el índice de morosidad? "),
                         "Es el porcentaje de créditos que están en mora (con atraso en pago). "
                         "Un índice < 2% indica sistema sano; entre 2-4% requiere precaución; "
                         f"y > 4% es señal de alerta sistémica. Valor actual del sistema: {mora_actual}. "
                         "La regulación de la SB exige provisiones crecientes según el nivel de riesgo."],
                        [html.Strong("¿Qué revela el treemap sectorial? "),
                         "Muestra qué sectores económicos concentran más crédito. "
                         "Una alta concentración en consumo personal o turismo puede "
                         "crear vulnerabilidades en períodos de crisis. La diversificación "
                         "sectorial reduce el riesgo sistémico del portafolio de créditos."],
                        [html.Strong("¿Qué dice la brecha de género? "),
                         "El crédito a mujeres representa ~35% del saldo total, lo que "
                         "refleja barreras estructurales de acceso al financiamiento formal. "
                         "Esta brecha es un indicador clave de inclusión financiera y "
                         "objetivo de política pública en la agenda del Gobierno dominicano."],
                    ]
                ),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_cal),    md=12, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_sector), md=6,  className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_gen),    md=6,  className="mb-3"),
                ]),
            ])

        # ── Indicadores ───────────────────────────────────────────────────────
        elif tab == "tab-indicadores":
            df = az.evolucion_indicadores()
            if df.empty:
                return dbc.Alert("Sin datos de indicadores. Ejecuta el ETL.", color="warning")

            tipos = df["tipo_indicador"].unique().tolist()
            figs = []
            for tipo in tipos:
                sub = df[df["tipo_indicador"] == tipo]

                if tipo == "financieros":
                    _ALTA = {"Activos Netos Totales / Patrimonio Neto"}
                    _PCT  = {
                        "Margen de Intermediación Neto",
                        "Spread de Tasas de Interés",
                        "Activos Improductivos / Patrimonio Neto",
                    }

                    sub_alta = sub[sub["nombre"].isin(_ALTA)]
                    if not sub_alta.empty:
                        fig_alta = px.line(
                            sub_alta, x="periodo", y="valor_promedio", color="nombre",
                            title="Indicadores Financieros — Apalancamiento (Activos / Patrimonio)",
                            labels={"valor_promedio": "Veces (x)", "periodo": "Período",
                                    "nombre": "Indicador"},
                        )
                        fig_alta.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                        _add_covid_band(fig_alta)
                        figs.append(dbc.Col(dcc.Graph(figure=fig_alta), md=12, className="mb-3"))

                    sub_pct = sub[sub["nombre"].isin(_PCT)]
                    if not sub_pct.empty:
                        fig_pct = px.line(
                            sub_pct, x="periodo", y="valor_promedio", color="nombre",
                            title="Indicadores Financieros — Escala Porcentual (%)",
                            labels={"valor_promedio": "Porcentaje (%)", "periodo": "Período",
                                    "nombre": "Indicador"},
                        )
                        fig_pct.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                        _add_covid_band(fig_pct)
                        figs.append(dbc.Col(dcc.Graph(figure=fig_pct), md=12, className="mb-3"))
                else:
                    fig = px.line(
                        sub, x="periodo", y="valor_promedio", color="nombre",
                        title=f"Indicadores — {tipo.title()}",
                        labels={"valor_promedio": "Valor", "periodo": "Período"},
                    )
                    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                    _add_covid_band(fig)
                    figs.append(dbc.Col(dcc.Graph(figure=fig), md=12, className="mb-3"))

            return html.Div([
                _info_card(
                    "¿Qué significan los indicadores prudenciales?",
                    [
                        [html.Strong("ROA (Return on Assets): "),
                         "Mide la rentabilidad sobre activos totales. En banca dominicana, "
                         "un ROA > 1.5% es saludable. Un ROA < 1% puede indicar problemas "
                         "de eficiencia operativa o alta carga de provisiones por morosidad."],
                        [html.Strong("ROE (Return on Equity): "),
                         "Mide el retorno sobre el capital propio de los accionistas. "
                         "Un ROE > 12% es competitivo en RD. Valores muy altos (> 25%) "
                         "pueden indicar apalancamiento excesivo más que eficiencia real."],
                        [html.Strong("Apalancamiento: "),
                         "El apalancamiento financiero (~8-9x) mide cuántas veces el activo "
                         "supera al capital propio. Un valor alto implica mayor retorno pero "
                         "también mayor exposición al riesgo sistémico. Se grafica en escala "
                         "separada ya que su magnitud difiere del resto de indicadores."],
                    ]
                ),
                dbc.Row(figs),
            ])

        # ── Solvencia ─────────────────────────────────────────────────────────
        elif tab == "tab-solvencia":
            df = az.solvencia_sistema()
            if df.empty:
                return dbc.Alert("Sin datos de solvencia. Ejecuta el ETL.", color="warning")

            # "Ajuste" es un factor de corrección regulatoria que puede ser negativo;
            # excluirlo de los boxplots y del gráfico de líneas
            _EXCLUIR_SOL = {"Ajuste"}
            # Abreviar nombres largos de componentes para la leyenda
            _SOL_SHORT = {
                "Activos y contingentes ponderados por riesgo crediticio y deducciones al patrimonio":
                    "APR (crédito, con deducciones)",
                "Activos y contingentes ponderados por riesgo crediticio y riesgo de mercado":
                    "APR (crédito + mercado)",
                "Capital requerido por riesgo de mercado":
                    "Cap. requerido (mercado)",
            }
            df_plot = df[~df["componente"].isin(_EXCLUIR_SOL)].copy()
            df_plot["comp_label"] = df_plot["componente"].map(
                lambda c: _SOL_SHORT.get(c, c)
            )
            comp_avgs = df_plot.groupby("componente")["promedio"].mean()
            comps_grandes = set(comp_avgs[comp_avgs > 100].index)
            comps_chicos  = set(comp_avgs[comp_avgs <= 100].index)

            # Gráfico de líneas con eje dual
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            color_map = [COLORS["azul_sb"], COLORS["rojo"], COLORS["dorado"],
                         COLORS["verde"], COLORS["gris"]]
            for idx, comp in enumerate(df_plot["componente"].unique()):
                sub = df_plot[df_plot["componente"] == comp]
                is_grande = comp in comps_grandes
                fig.add_trace(
                    go.Scatter(
                        x=sub["periodo"], y=sub["promedio"],
                        name=sub["comp_label"].iloc[0], mode="lines",
                        line={"color": color_map[idx % len(color_map)], "width": 2},
                    ),
                    secondary_y=not is_grande,
                )
            fig.update_yaxes(title_text="RD$ MM — APR / Patrimonio", secondary_y=False)
            fig.update_yaxes(title_text="", secondary_y=True)
            fig.update_layout(
                title="Evolución de la Solvencia del Sistema Financiero",
                plot_bgcolor="white", paper_bgcolor="white",
                legend={
                    "orientation": "h",
                    "yanchor": "top", "y": -0.22,
                    "font": {"size": 9},
                },
                margin={"b": 160},
            )
            _add_covid_band(fig)

            # Boxplot grande (APR / Patrimonio)
            df_grandes = df_plot[df_plot["componente"].isin(comps_grandes)]
            fig_box1 = go.Figure()
            for comp in sorted(comps_grandes):
                sub = df_grandes[df_grandes["componente"] == comp]
                label = _SOL_SHORT.get(comp, comp)
                fig_box1.add_trace(go.Box(y=sub["promedio"], name=label, boxpoints="outliers"))
            fig_box1.update_layout(
                title="Distribución — Componentes de Gran Escala (RD$ MM)",
                yaxis_title="RD$ (millones)",
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis_tickangle=30,
                margin={"b": 120},
                showlegend=False,
            )

            # Boxplot chico (índice de solvencia porcentual)
            df_chicos = df_plot[df_plot["componente"].isin(comps_chicos)]
            fig_box2 = go.Figure()
            for comp in sorted(comps_chicos):
                sub = df_chicos[df_chicos["componente"] == comp]
                label = _SOL_SHORT.get(comp, comp)
                fig_box2.add_trace(go.Box(y=sub["promedio"], name=label, boxpoints="outliers"))
            fig_box2.update_layout(
                title="Distribución — Índices de Solvencia (Tier 1, Tier 2, IS)",
                yaxis_title="Ratio / Índice",
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis_tickangle=30,
                margin={"b": 100},
                showlegend=False,
            )

            return html.Div([
                _info_card(
                    "¿Qué es la solvencia bancaria y por qué importa?",
                    [
                        [html.Strong("¿Qué es el Índice de Solvencia? "),
                         "Es el ratio entre el capital regulatorio y los activos ponderados "
                         "por riesgo (APR). Mide la capacidad del banco para absorber "
                         "pérdidas inesperadas sin quebrar. La Ley Monetaria de RD exige "
                         "mínimo 10%, pero el BCRD recomienda mantener > 12%."],
                        [html.Strong("¿Qué son Tier 1 y Tier 2? "),
                         "Tier 1 es el capital de mayor calidad: acciones ordinarias y "
                         "reservas retenidas. Tier 2 incluye instrumentos subordinados y "
                         "reservas genéricas. Basilea III (adoptado por el BCRD) prioriza "
                         "el Tier 1 como la primera línea de defensa ante pérdidas."],
                        [html.Strong("¿Por qué eje dual en el gráfico de líneas? "),
                         "Activos Ponderados por Riesgo y Patrimonio Técnico se expresan "
                         "en RD$ millones (escala 10k-80k), mientras Índice de Solvencia "
                         "y los Tier se expresan como ratio (escala 0-0.5). El eje dual "
                         "permite visualizar ambas escalas sin que ninguna quede aplastada."],
                    ]
                ),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig), md=12, className="mb-3"),
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_box1), md=6, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_box2), md=6, className="mb-3"),
                ]),
            ])

        # ── Estadísticas ──────────────────────────────────────────────────────
        elif tab == "tab-stats":
            analyzer = get_analyzer()
            stats = analyzer.estadisticas_descriptivas()
            skew_cap = stats.get("captaciones", {}).get("skewness", 0)

            df_corr = analyzer.correlacion_macro_banca()
            fig_heat = go.Figure()
            if not df_corr.empty:
                fig_heat = go.Figure(go.Heatmap(
                    z=df_corr.values,
                    x=df_corr.columns.tolist(),
                    y=df_corr.index.tolist(),
                    colorscale="RdBu", zmid=0,
                    text=df_corr.round(2).values,
                    texttemplate="%{text}",
                    colorbar={"title": "r"},
                ))
                fig_heat.update_layout(
                    title="Correlación Cruzada — Variables Macro y Bancarias",
                    plot_bgcolor="white", paper_bgcolor="white",
                    height=450,
                )

            df_hist = analyzer.histograma_datos("captaciones", "monto", bins=40)
            fig_hist = go.Figure()
            if not df_hist.empty:
                fig_hist.add_trace(go.Bar(
                    x=df_hist["bin_mid"], y=df_hist["frecuencia"],
                    name="Frecuencia",
                    marker_color=COLORS["azul_sb"], opacity=0.8,
                    width=(df_hist["bin_right"] - df_hist["bin_left"]).mean() * 0.9,
                ))
            fig_hist.update_layout(
                title="Distribución de Montos de Captación",
                xaxis_title="Monto (RD$)", yaxis_title="Frecuencia",
                plot_bgcolor="white", paper_bgcolor="white",
            )

            df_out = analyzer.detectar_outliers("captaciones", "monto")
            outlier_section = []
            if not df_out.empty:
                outlier_section = [
                    html.H5("Outliers Detectados (IQR + Z-score)",
                            className="mt-4 mb-2", style={"color": COLORS["rojo"]}),
                    dbc.Alert(
                        f"{len(df_out)} registros atípicos detectados "
                        f"(de {stats.get('captaciones',{}).get('count',0):,.0f} totales)",
                        color="warning", className="mb-2"
                    ),
                    dbc.Table(
                        [html.Thead(html.Tr([
                            html.Th("Entidad"), html.Th("Fecha"),
                            html.Th("Monto (RD$)"), html.Th("Z-score"),
                        ]))] +
                        [html.Tbody([
                            html.Tr([
                                html.Td(str(row.get("entidad",""))),
                                html.Td(str(row.get("fecha",""))[:10]),
                                html.Td(f"{row.get('monto',0):,.2f}"),
                                html.Td(f"{row.get('z_score',0):.2f}"),
                            ])
                            for _, row in df_out.head(15).iterrows()
                        ])],
                        bordered=True, striped=True, hover=True, className="table-sm"
                    ),
                ]

            desc_rows = []
            metrics = ["count","mean","std","min","25%","50%","75%","max","skewness","kurtosis"]
            for tabla, s in stats.items():
                desc_rows.append(html.H5(
                    tabla.replace("_"," ").title(), className="mt-4 mb-2",
                    style={"color": COLORS["azul_sb"]}
                ))
                t_rows = []
                for m in metrics:
                    if m in s:
                        val = s[m]
                        t_rows.append(html.Tr([
                            html.Td(m.replace("_"," ").title(),
                                    style={"fontWeight":"600","width":"30%"}),
                            html.Td(f"{val:,.4f}" if isinstance(val, float) else str(val)),
                        ]))
                desc_rows.append(dbc.Table(
                    [html.Tbody(t_rows)],
                    bordered=True, hover=True, striped=True, className="table-sm"
                ))

            return html.Div([
                _info_card(
                    "¿Cómo interpretar las estadísticas del sistema?",
                    [
                        [html.Strong("Skewness (asimetría): "),
                         f"El valor de skewness en captaciones es {skew_cap:.2f}, lo que indica "
                         "una distribución muy sesgada a la derecha: pocos bancos grandes "
                         "concentran montos enormes, mientras la mayoría tiene valores "
                         "moderados. Una distribución normal tiene skewness = 0; "
                         "valores > 1 indican asimetría significativa."],
                        [html.Strong("Kurtosis (apuntamiento): "),
                         "La kurtosis mide qué tan 'puntiaguda' es la distribución. "
                         "Una kurtosis > 3 (leptocúrtica) indica colas pesadas: hay más "
                         "valores extremos de lo esperado. Esto es típico en datos "
                         "financieros y justifica el análisis de outliers."],
                        [html.Strong("Heatmap de correlación: "),
                         "Los colores rojos intensos indican correlación positiva fuerte "
                         "(variables que suben juntas), azules indican correlación negativa "
                         "(se mueven en direcciones opuestas). La diagonal siempre es 1.0 "
                         "ya que toda variable se correlaciona perfectamente consigo misma."],
                    ]
                ),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_heat), md=7, className="mb-3"),
                    dbc.Col(dcc.Graph(figure=fig_hist), md=5, className="mb-3"),
                ]),
                *outlier_section,
                html.Hr(),
                html.Div(desc_rows, className="px-2"),
            ])

        # ── Tabs externos ─────────────────────────────────────────────────────
        elif tab == "tab-macro":
            try:
                return macro_banca.render(az)
            except Exception as e:
                return dbc.Alert(f"Error en Macro vs Banca: {e}", color="danger")

        elif tab == "tab-ranking":
            try:
                return ranking.render(az)
            except Exception as e:
                return dbc.Alert(f"Error en Ranking: {e}", color="danger")

        elif tab == "tab-mapa":
            try:
                return mapa.render(az)
            except Exception as e:
                return dbc.Alert(f"Error en Mapa Provincial: {e}", color="danger")

        elif tab == "tab-remesas":
            try:
                return remesas.render(az)
            except Exception as e:
                return dbc.Alert(f"Error en Remesas: {e}", color="danger")

        elif tab == "tab-stress":
            try:
                return stress.render(az)
            except Exception as e:
                return dbc.Alert(f"Error en Stress Testing: {e}", color="danger")

        return html.Div("Selecciona una pestaña.")


# ── Factory ───────────────────────────────────────────────────────────────────

def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="SIF-Bancario · RD",
        suppress_callback_exceptions=True,
    )
    app.layout = build_layout()
    register_callbacks(app)
    az = get_analyzer()
    stress.register_stress_callback(app, az)
    ranking.register_ranking_callback(app, az)
    return app


def run():
    app = create_app()
    logger.info("Dashboard disponible en http://%s:%d", DASH_HOST, DASH_PORT)
    app.run(host=DASH_HOST, port=DASH_PORT, debug=DASH_DEBUG)
