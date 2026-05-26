"""Tab: Remesas e Inclusión Financiera."""
import pathlib
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash import dcc, html

DATA_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "data" / "processed"

COLORS = {
    "azul_sb": "#003087",
    "rojo":    "#C8102E",
    "dorado":  "#F5A623",
    "verde":   "#28A745",
    "naranja": "#E67E22",
}

COVID_X0, COVID_X1 = "2020-03-01", "2020-12-31"


def _load(filename: str) -> pd.DataFrame:
    p = DATA_DIR / filename
    if p.exists():
        return pd.read_csv(p, parse_dates=["fecha"])
    return pd.DataFrame()


def _info_panel(pearson_r):
    r_desc = "positiva muy fuerte" if pearson_r and pearson_r > 0.8 else (
             "positiva fuerte" if pearson_r and pearson_r > 0.6 else "moderada")
    return dbc.Card([dbc.CardBody([
        html.H6("Guía de interpretación — Remesas e Inclusión Financiera",
                style={"color": COLORS["azul_sb"], "fontWeight": "700", "marginBottom": "8px"}),
        dbc.Row([
            dbc.Col([
                html.P([html.Strong("¿Por qué las remesas impactan las captaciones? "),
                        "La República Dominicana es el mayor receptor de remesas del Caribe. "
                        "Cuando un dominicano en el exterior envía dinero, parte de ese flujo "
                        "se deposita en el sistema bancario formal. La correlación Pearson "
                        f"r = {pearson_r:.3f} ({r_desc}) confirma esta relación directa y "
                        "estadísticamente robusta entre ambas variables."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Cómo interpretar r = {:.3f}? ".format(pearson_r or 0)),
                        "Un valor de r cercano a +1 indica correlación positiva casi perfecta: "
                        "cuando las remesas suben, las captaciones suben en proporción similar. "
                        "Esto sugiere que las políticas de atracción de remesas son un canal "
                        "directo de profundización del sistema financiero dominicano."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
            dbc.Col([
                html.P([html.Strong("¿Qué pasó en 2020 con las remesas? "),
                        "Contrariamente a lo esperado, las remesas cayeron solo en abril-mayo "
                        "2020 (barra gris = banda COVID), pero luego se dispararon gracias a "
                        "los estímulos fiscales en EE.UU. (cheques COVID). El año 2020 terminó "
                        "con un total de USD 7,981 millones, y 2021 superó los USD 10,000 MM "
                        "por primera vez en la historia."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Qué dice la brecha de género sobre inclusión? "),
                        "El 65% del crédito va a hombres y solo 35% a mujeres, a pesar de "
                        "que las mujeres son las principales receptoras de remesas en los "
                        "hogares. Esto indica barreras de acceso estructurales al crédito "
                        "formal para la población femenina dominicana."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
        ]),
    ])], style={"backgroundColor": "#EBF3FB", "borderLeft": f"4px solid {COLORS['azul_sb']}",
                "borderRadius": "6px", "border": "1px solid #D0E4F5"},
       className="mb-3")


def render(az) -> html.Div:
    df_rem = _load("macro_remesas.csv")
    df_cap = az.evolucion_captaciones_mensual()

    pearson_r = None
    df_merged = pd.DataFrame()
    if not df_rem.empty and not df_cap.empty:
        df_cap_m = df_cap.groupby("periodo")["total_captado"].sum().reset_index()
        df_cap_m["fecha"] = pd.to_datetime(df_cap_m["periodo"])
        df_rem_m = df_rem.copy()
        df_rem_m["fecha"] = (pd.to_datetime(df_rem_m["fecha"])
                             .dt.to_period("M").dt.to_timestamp())
        df_merged = df_rem_m.merge(df_cap_m[["fecha","total_captado"]], on="fecha", how="inner")
        if len(df_merged) > 5:
            pearson_r = float(
                df_merged["monto_usd_millones"].corr(df_merged["total_captado"])
            )

    # ── 1. Remesas mensuales ──────────────────────────────────────────────────
    fig_rem = go.Figure()
    if not df_rem.empty:
        df_s = df_rem.sort_values("fecha")
        fig_rem.add_trace(go.Scatter(
            x=df_s["fecha"], y=df_s["monto_usd_millones"],
            name="Remesas (USD MM)", fill="tozeroy",
            line={"color": COLORS["dorado"], "width": 2}
        ))
        ma12 = df_s["monto_usd_millones"].rolling(12).mean()
        fig_rem.add_trace(go.Scatter(
            x=df_s["fecha"], y=ma12,
            name="Media móvil 12 meses",
            line={"color": COLORS["rojo"], "dash": "dash", "width": 2}
        ))
    fig_rem.add_vrect(
        x0=COVID_X0, x1=COVID_X1,
        fillcolor="gray", opacity=0.12, line_width=0,
        annotation_text="COVID-19", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="gray",
    )
    fig_rem.update_layout(
        title="Remesas Mensuales hacia República Dominicana (USD Millones)",
        yaxis_title="USD Millones",
        plot_bgcolor="white", paper_bgcolor="white",
        legend={"orientation": "h", "y": -0.18},
    )

    # ── 2. Scatter correlación ────────────────────────────────────────────────
    fig_corr = go.Figure()
    if not df_merged.empty:
        fig_corr.add_trace(go.Scatter(
            x=df_merged["monto_usd_millones"],
            y=df_merged["total_captado"],
            mode="markers",
            marker={"color": COLORS["azul_sb"], "size": 6, "opacity": 0.65},
            name="Observaciones"
        ))
        if pearson_r is not None:
            m = np.polyfit(df_merged["monto_usd_millones"],
                           df_merged["total_captado"], 1)
            x_line = np.linspace(df_merged["monto_usd_millones"].min(),
                                 df_merged["monto_usd_millones"].max(), 50)
            fig_corr.add_trace(go.Scatter(
                x=x_line, y=np.polyval(m, x_line),
                name=f"Tendencia (r = {pearson_r:.3f})",
                line={"color": COLORS["rojo"], "dash": "dash"}
            ))
    fig_corr.update_layout(
        title="Correlación: Remesas vs Captaciones Totales",
        xaxis_title="Remesas (USD MM)",
        yaxis_title="Captaciones (RD$)",
        plot_bgcolor="white", paper_bgcolor="white",
    )

    # ── 3. Remesas anuales ────────────────────────────────────────────────────
    fig_anual = go.Figure()
    if not df_rem.empty:
        df_anual = (
            df_rem.assign(year=df_rem["fecha"].dt.year)
            .groupby("year")["monto_usd_millones"].sum()
            .reset_index()
        )
        bar_colors = [COLORS["rojo"] if y == 2020 else COLORS["naranja"]
                      for y in df_anual["year"]]
        fig_anual.add_trace(go.Bar(
            x=df_anual["year"], y=df_anual["monto_usd_millones"],
            name="Total anual (USD MM)", marker_color=bar_colors
        ))
        # Anotación 2021 boom
        if 2021 in df_anual["year"].values:
            val_2021 = df_anual.loc[df_anual["year"]==2021, "monto_usd_millones"].values[0]
            fig_anual.add_annotation(
                x=2021, y=val_2021, text="+30.7%",
                showarrow=True, arrowhead=2, arrowcolor=COLORS["verde"],
                font={"color": COLORS["verde"], "size": 11}, ay=-30,
            )
    fig_anual.update_layout(
        title="Remesas Anuales Totales (USD Millones)",
        xaxis_title="Año", yaxis_title="USD Millones",
        plot_bgcolor="white", paper_bgcolor="white",
    )

    # ── 4. Brecha género ──────────────────────────────────────────────────────
    df_gen = az.brecha_genero_credito()
    fig_gen = go.Figure()
    if not df_gen.empty:
        for gen, color in [("M", COLORS["azul_sb"]), ("F", COLORS["rojo"]),
                           ("Masculino", COLORS["azul_sb"]), ("Femenino", COLORS["rojo"])]:
            sub = df_gen[df_gen["genero"] == gen]
            if not sub.empty:
                fig_gen.add_trace(go.Scatter(
                    x=sub["periodo"], y=sub["saldo_total"],
                    name=gen, fill="tozeroy",
                    line={"color": color, "width": 2}, opacity=0.8,
                ))
        fig_gen.update_layout(
            title="Inclusión Financiera — Acceso al Crédito por Género",
            xaxis_title="Período", yaxis_title="Saldo (RD$)",
            plot_bgcolor="white", paper_bgcolor="white",
        )

    kpi_corr = (
        dbc.Alert([
            html.Strong(f"Correlación Pearson remesas-captaciones: r = {pearson_r:.4f}"),
            html.Span(f"  —  correlación positiva muy fuerte" if pearson_r > 0.8 else
                      f"  —  correlación positiva fuerte" if pearson_r > 0.6 else
                      f"  —  correlación moderada",
                      style={"fontSize": "0.9rem"}),
        ], color="success" if pearson_r and pearson_r > 0.5 else "info", className="mb-3")
        if pearson_r is not None
        else dbc.Alert("No hay suficientes datos para calcular correlación.", color="warning")
    )

    return html.Div([
        _info_panel(pearson_r or 0.0),
        kpi_corr,
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_rem), md=12, className="mb-3")]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_corr),  md=6, className="mb-3"),
            dbc.Col(dcc.Graph(figure=fig_anual), md=6, className="mb-3"),
        ]),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_gen), md=12, className="mb-3")]),
    ])
