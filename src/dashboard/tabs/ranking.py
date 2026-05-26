"""Tab: Ranking Bancario — scorecard interactivo por entidad y año."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

COLORS = {
    "azul_sb": "#003087",
    "rojo":    "#C8102E",
    "dorado":  "#F5A623",
    "verde":   "#28A745",
}

MEDAL_COLORS = ["#FFD700", "#C0C0C0", "#CD7F32"]


def _info_panel():
    return dbc.Card([dbc.CardBody([
        html.H6("Guía de interpretación — Ranking Bancario",
                style={"color": COLORS["azul_sb"], "fontWeight": "700", "marginBottom": "8px"}),
        dbc.Row([
            dbc.Col([
                html.P([html.Strong("¿Cómo leer el scorecard? "),
                        "El ranking ordena las entidades financieras por captaciones totales "
                        "acumuladas en el período seleccionado. Las flechas indican la "
                        "tendencia relativa: ▲ para los líderes del mercado (top tercio), "
                        "► para posiciones medias, y ▼ para los de menor participación. "
                        "El % de mercado muestra la cuota sobre el total del sistema."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Qué dice la concentración sobre la competencia? "),
                        "En República Dominicana, los 3 principales bancos (BPD, BRE, BHD) "
                        "concentran ~59% del total de captaciones. Este nivel de concentración "
                        "(similar al Índice HHI > 1.800) se clasifica como mercado concentrado "
                        "según los estándares del DOJ/FTC, lo que puede impactar "
                        "negativamente las tasas que reciben los depositantes."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
            dbc.Col([
                html.P([html.Strong("¿Qué muestran los podios Top 3 / Bottom 3? "),
                        "El top 3 (bancos líderes) opera con economías de escala, "
                        "redes de sucursales extensas y acceso a fondeo más barato. "
                        "El bottom 3 son generalmente entidades especializadas (bancos de "
                        "ahorro y crédito o asociaciones) que atienden nichos específicos "
                        "y micro-segmentos con menor penetración."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Cómo usar el selector de año? "),
                        "Selecciona un año específico para ver cómo era el ranking en ese "
                        "período. Observa cómo el COVID-2020 y el ciclo TPM-2022 "
                        "modificaron las posiciones relativas de las entidades. "
                        "Los cambios históricos reflejan estrategias y resiliencias distintas."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
        ]),
    ])], style={"backgroundColor": "#EBF3FB", "borderLeft": f"4px solid {COLORS['azul_sb']}",
                "borderRadius": "6px", "border": "1px solid #D0E4F5"},
       className="mb-3")


def _build_ranking(df_top: pd.DataFrame):
    if df_top.empty:
        return [], [], go.Figure(), go.Figure()

    df_top = df_top.reset_index(drop=True)
    df_top["rank"] = df_top.index + 1
    df_top["pct_total"] = (
        df_top["total_captado"] / df_top["total_captado"].sum() * 100
    ).round(2)

    # Top 3 cards
    top3_cards = []
    for i, (_, row) in enumerate(df_top.head(3).iterrows()):
        medal = ["1er", "2do", "3er"][i]
        monto_fmt = f"RD$ {row['total_captado']/1_000:.1f} mil MM"
        top3_cards.append(
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H4(medal, style={"color": MEDAL_COLORS[i], "textAlign": "center",
                                      "fontWeight": "900", "marginBottom": "4px"}),
                html.H5(row["entidad"], className="text-center mb-1",
                        style={"color": MEDAL_COLORS[i], "fontWeight": "bold",
                               "fontSize": "0.95rem"}),
                html.P(monto_fmt, className="text-center text-muted mb-0",
                       style={"fontSize": "0.85rem"}),
                html.P(f"{row['pct_total']:.1f}% del mercado",
                       className="text-center mb-0",
                       style={"fontSize": "0.75rem", "color": COLORS["verde"]}),
            ])], className="shadow-sm border-0 h-100"), md=4)
        )

    # Bottom 3 cards
    bot3_cards = []
    for _, row in df_top.tail(3).iloc[::-1].iterrows():
        monto_fmt = f"RD$ {row['total_captado']/1_000:.1f} mil MM"
        bot3_cards.append(
            dbc.Col(dbc.Card([dbc.CardBody([
                html.H5(row["entidad"], className="text-center mb-1",
                        style={"color": COLORS["rojo"], "fontSize": "0.9rem"}),
                html.P(monto_fmt, className="text-center text-muted mb-0",
                       style={"fontSize": "0.85rem"}),
                html.P(f"{row['pct_total']:.2f}% del mercado",
                       className="text-center mb-0",
                       style={"fontSize": "0.75rem", "color": COLORS["rojo"]}),
            ])], className="shadow-sm border-0 h-100"), md=4)
        )

    # Bar chart ranking
    fig_rank = px.bar(
        df_top, x="total_captado", y="entidad", orientation="h",
        title="Ranking por Captaciones",
        labels={"total_captado": "Total Captado (RD$)", "entidad": "Entidad"},
        color="pct_total", color_continuous_scale="Blues",
        text=df_top["rank"].apply(lambda r: f"#{r}"),
    )
    fig_rank.update_layout(
        yaxis={"categoryorder": "total ascending"},
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False, height=560,
    )
    fig_rank.update_traces(textposition="outside")

    # Pie cuota de mercado
    fig_pie = px.pie(
        df_top.head(8),
        values="total_captado", names="entidad",
        title="Cuota de Mercado (Top 8)",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")

    return top3_cards, bot3_cards, fig_rank, fig_pie


def render(az) -> html.Div:
    df_all = az.top_entidades_captaciones(n=21)

    top3_cards, bot3_cards, fig_rank, fig_pie = _build_ranking(df_all)

    # Años disponibles (para el selector)
    years = list(range(2015, 2026))

    # Tabla scorecard all-time
    tabla_rows = []
    if not df_all.empty:
        df_all = df_all.reset_index(drop=True)
        df_all["rank"] = df_all.index + 1
        df_all["pct_total"] = (
            df_all["total_captado"] / df_all["total_captado"].sum() * 100
        ).round(2)
        for _, row in df_all.iterrows():
            r = int(row["rank"])
            trend = "▲" if r <= 7 else ("►" if r <= 14 else "▼")
            trend_color = (COLORS["verde"] if trend == "▲"
                           else (COLORS["dorado"] if trend == "►" else COLORS["rojo"]))
            tabla_rows.append(html.Tr([
                html.Td(f"#{r}", style={"fontWeight": "bold", "width": "6%"}),
                html.Td(row["entidad"], style={"width": "35%"}),
                html.Td(f"RD$ {row['total_captado']/1_000:,.1f} mil MM",
                        style={"width": "28%"}),
                html.Td(f"{row['pct_total']:.2f}%", style={"width": "18%"}),
                html.Td(trend, style={"color": trend_color, "fontSize": "1.1rem",
                                      "width": "13%", "textAlign": "center"}),
            ]))

    return html.Div([
        _info_panel(),

        # Podio
        html.H5("Podio — Top 3 Entidades (acumulado 2015-2025)",
                className="mb-3 mt-2", style={"color": COLORS["azul_sb"]}),
        dbc.Row(top3_cards, className="mb-4 g-3"),

        html.H5("Menores Participantes del Mercado",
                className="mb-3", style={"color": COLORS["rojo"]}),
        dbc.Row(bot3_cards, className="mb-4 g-3"),

        html.Hr(),

        # Selector de año
        dbc.Card([
            dbc.CardHeader("Ranking Histórico por Año — Selecciona un período",
                           style={"fontWeight": "bold", "backgroundColor": "#F8F9FA"}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Año:", style={"fontWeight": "600", "marginRight": "12px"}),
                        dcc.Dropdown(
                            id="ranking-year-select",
                            options=[{"label": str(y), "value": y} for y in years],
                            value=2024,
                            clearable=False,
                            style={"width": "160px", "display": "inline-block"},
                        ),
                    ], className="d-flex align-items-center"),
                ], className="mb-3"),
                html.Div(id="ranking-year-content"),
            ]),
        ], className="shadow-sm mb-4"),

        html.Hr(),

        # Gráficos acumulados
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_rank), md=8, className="mb-3"),
            dbc.Col(dcc.Graph(figure=fig_pie),  md=4, className="mb-3"),
        ]),

        # Scorecard
        html.H5("Scorecard Completo — Acumulado 2015-2025",
                className="mb-2", style={"color": COLORS["azul_sb"]}),
        dbc.Table(
            [html.Thead(html.Tr([
                html.Th("#"), html.Th("Entidad"), html.Th("Total Captado"),
                html.Th("% Mercado"), html.Th("Trend"),
            ]))] +
            [html.Tbody(tabla_rows)],
            bordered=True, hover=True, striped=True, className="table-sm"
        ) if tabla_rows else dbc.Alert("Sin datos disponibles.", color="info"),
    ])


def register_ranking_callback(app, az):
    @app.callback(
        Output("ranking-year-content", "children"),
        Input("ranking-year-select", "value"),
    )
    def update_year_ranking(year):
        if year is None:
            return html.Div()
        try:
            df = az.evolucion_captaciones_mensual()
            if df.empty:
                return dbc.Alert(f"Sin datos para el año {year}.", color="info")

            df_year = df[df["periodo"].str.startswith(str(year))]
            if df_year.empty:
                return dbc.Alert(f"Sin datos para el año {year}.", color="info")

            # Agrupamos por entidad (necesitamos top_entidades para ese año)
            df_raw = az._csv("captaciones")
            if df_raw.empty:
                return dbc.Alert("Sin datos detallados.", color="info")

            df_yr = df_raw[
                (df_raw["fuente_endpoint"] == "captaciones_moneda") &
                (pd.to_datetime(df_raw["fecha"]).dt.year == year)
            ]
            if df_yr.empty:
                return dbc.Alert(f"Sin datos para el año {year}.", color="info")

            df_ent = (
                df_yr.groupby("entidad")["monto"]
                .sum().reset_index(name="total_captado")
                .sort_values("total_captado", ascending=False)
            )

            top3_c, bot3_c, fig_r, fig_p = _build_ranking(df_ent)

            return html.Div([
                html.H6(f"Ranking año {year}",
                        className="mt-2 mb-3",
                        style={"color": COLORS["azul_sb"], "fontWeight": "700"}),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_r), md=8),
                    dbc.Col(dcc.Graph(figure=fig_p), md=4),
                ]),
            ])
        except Exception as e:
            return dbc.Alert(f"Error al cargar ranking {year}: {e}", color="danger")
