"""Tab: Macro vs Banca — TPM, IPC, tipo de cambio vs indicadores bancarios."""
import pathlib
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

# Eventos clave para anotar
EVENTOS = [
    ("2020-03-01", "COVID-19\nmar-2020",   "gray"),
    ("2020-10-01", "Recuperación\noct-2020","#28A745"),
    ("2022-06-01", "Pico inflación\njun-2022", "#C8102E"),
    ("2023-01-01", "Normalización\n2023",   "#003087"),
]

COVID_X0, COVID_X1 = "2020-03-01", "2020-12-31"


def _load(filename: str) -> pd.DataFrame:
    p = DATA_DIR / filename
    if p.exists():
        return pd.read_csv(p, parse_dates=["fecha"])
    return pd.DataFrame()


def _add_covid_band(fig):
    fig.add_vrect(
        x0=COVID_X0, x1=COVID_X1,
        fillcolor="gray", opacity=0.12, line_width=0,
        annotation_text="COVID-19", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="gray",
    )
    return fig


def _add_eventos(fig, y_alts=None):
    """Añade líneas verticales con anotaciones para eventos clave.
    y_alts permite personalizar las alturas para evitar solapamiento."""
    if y_alts is None:
        y_alts = [1.10, 1.02, 1.10, 1.02]
    for i, (x, texto, color) in enumerate(EVENTOS):
        fig.add_vline(x=x, line_dash="dot", line_color=color, line_width=1.2)
        fig.add_annotation(
            x=x, y=y_alts[i], yref="paper",
            text=texto.replace("\n", " "),
            showarrow=False,
            font={"size": 8, "color": color},
            xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            borderpad=2,
        )
    return fig


def _info_panel():
    return dbc.Card([dbc.CardBody([
        html.H6("Guía de interpretación — Macro vs Banca",
                style={"color": COLORS["azul_sb"], "fontWeight": "700", "marginBottom": "8px"}),
        dbc.Row([
            dbc.Col([
                html.P([html.Strong("¿Qué es la TPM? "),
                        "La Tasa de Política Monetaria es el instrumento principal del "
                        "BCRD para controlar la inflación. Cuando sube, los préstamos se "
                        "encarecen y el crédito se contrae; cuando baja, se estimula la "
                        "economía. Los bancos ajustan sus tasas activas y pasivas siguiendo "
                        "la TPM con un rezago de 1-3 meses."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Cómo afecta la inflación a los bancos? "),
                        "Una inflación alta (> 6%) erosiona el valor real de los depósitos "
                        "y obliga al BCRD a subir la TPM. Esto puede aumentar la morosidad "
                        "porque los deudores pagan cuotas más altas en términos nominales. "
                        "El pico fue 9.64% en 2022, el mayor en una década."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
            dbc.Col([
                html.P([html.Strong("¿Qué pasó en 2020? "),
                        "El COVID-19 provocó una contracción del PIB de -15.3% en Q2-2020. "
                        "El BCRD respondió con un corte de emergencia de 300 pb en la TPM "
                        "(de 4.50% a 3.00%) y alivios regulatorios. La banda sombreada gris "
                        "en todos los gráficos marca este período crítico."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Qué pasó en 2022? "),
                        "La guerra en Ucrania y la demanda post-pandemia dispararon la "
                        "inflación global. El BCRD subió la TPM de 3.00% a 8.50% en menos "
                        "de un año (+550 pb). Esto se traduce en mayor costo del crédito "
                        "y presión sobre los índices de morosidad bancaria."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
        ]),
    ])], style={"backgroundColor": "#EBF3FB", "borderLeft": f"4px solid {COLORS['azul_sb']}",
                "borderRadius": "6px", "border": "1px solid #D0E4F5"},
       className="mb-3")


def render(az) -> html.Div:
    df_tpm  = _load("macro_tasas.csv")
    df_ipc  = _load("macro_inflacion.csv")
    df_tc   = _load("macro_tipo_cambio.csv")
    df_mor  = az.calidad_cartera()

    # ── 1. TPM + IPC interanual ───────────────────────────────────────────────
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    if not df_tpm.empty:
        fig1.add_trace(go.Scatter(
            x=df_tpm["fecha"], y=df_tpm["tpm_nominal"],
            name="TPM (%)", line={"color": COLORS["azul_sb"], "width": 2}
        ), secondary_y=False)
    if not df_ipc.empty:
        fig1.add_trace(go.Scatter(
            x=df_ipc["fecha"], y=df_ipc["ipc_interanual_pct"],
            name="Inflación IPC interanual (%)",
            line={"color": COLORS["rojo"], "dash": "dash", "width": 2}
        ), secondary_y=True)
    _add_covid_band(fig1)
    _add_eventos(fig1)
    fig1.update_layout(
        title="Tasa de Política Monetaria vs Inflación (IPC interanual)",
        plot_bgcolor="white", paper_bgcolor="white",
        legend={"orientation": "h", "y": -0.18},
        margin={"t": 100},
    )
    fig1.update_yaxes(title_text="TPM (%)", secondary_y=False)
    fig1.update_yaxes(title_text="Inflación (%)", secondary_y=True)

    # ── 2. TPM vs Morosidad ───────────────────────────────────────────────────
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    if not df_tpm.empty:
        fig2.add_trace(go.Scatter(
            x=df_tpm["fecha"], y=df_tpm["tpm_nominal"],
            name="TPM (%)", line={"color": COLORS["azul_sb"], "width": 2}
        ), secondary_y=False)
    if not df_mor.empty and "indice_morosidad" in df_mor.columns:
        # Convertir periodo string a fecha
        df_m = df_mor.copy()
        try:
            df_m["fecha"] = pd.to_datetime(df_m["periodo"])
        except Exception:
            df_m["fecha"] = df_m["periodo"]
        fig2.add_trace(go.Scatter(
            x=df_m["fecha"], y=df_m["indice_morosidad"],
            name="Morosidad (%)",
            line={"color": COLORS["dorado"], "dash": "dot", "width": 2}
        ), secondary_y=True)
    _add_covid_band(fig2)
    # Alturas más escalonadas para el gráfico compacto (md=6)
    _add_eventos(fig2, y_alts=[1.13, 1.06, 0.99, 0.92])
    fig2.update_layout(
        title="Política Monetaria (TPM) vs Morosidad Bancaria",
        plot_bgcolor="white", paper_bgcolor="white",
        legend={"orientation": "h", "y": -0.18},
        margin={"t": 120},
    )
    fig2.update_yaxes(title_text="TPM (%)", secondary_y=False)
    fig2.update_yaxes(title_text="Morosidad (%)", secondary_y=True)

    # ── 3. Tipo de cambio ─────────────────────────────────────────────────────
    fig3 = go.Figure()
    if not df_tc.empty:
        fig3.add_trace(go.Scatter(
            x=df_tc["fecha"], y=df_tc["venta_dop_usd"],
            name="Venta (DOP/USD)", fill="tonexty",
            line={"color": COLORS["naranja"]}
        ))
        fig3.add_trace(go.Scatter(
            x=df_tc["fecha"], y=df_tc["compra_dop_usd"],
            name="Compra (DOP/USD)", fill="tozeroy",
            line={"color": COLORS["dorado"]}
        ))
    # Banda COVID sin anotación interna — etiqueta separada de tamaño reducido
    fig3.add_vrect(
        x0=COVID_X0, x1=COVID_X1,
        fillcolor="gray", opacity=0.12, line_width=0,
    )
    fig3.add_annotation(
        x=COVID_X0, y=0.97, yref="paper",
        text="COVID", showarrow=False,
        font={"size": 8, "color": "gray"},
        xanchor="left", bgcolor="rgba(255,255,255,0)",
    )
    fig3.update_layout(
        title="Tipo de Cambio DOP/USD — Evolución 2015-2025",
        yaxis_title="DOP por 1 USD",
        plot_bgcolor="white", paper_bgcolor="white",
        legend={"orientation": "h", "y": -0.18},
    )

    # ── 4. IPC mensual ────────────────────────────────────────────────────────
    fig4 = go.Figure()
    if not df_ipc.empty:
        colors_bar = [COLORS["rojo"] if v > 0 else COLORS["verde"]
                      for v in df_ipc["ipc_mensual_pct"]]
        fig4.add_trace(go.Bar(
            x=df_ipc["fecha"], y=df_ipc["ipc_mensual_pct"],
            name="IPC mensual (%)", marker_color=colors_bar
        ))
    _add_covid_band(fig4)
    fig4.update_layout(
        title="Variación Mensual del IPC",
        yaxis_title="Var. % mensual",
        plot_bgcolor="white", paper_bgcolor="white",
    )

    return html.Div([
        _info_panel(),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig1), md=12, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig2), md=6, className="mb-3"),
            dbc.Col(dcc.Graph(figure=fig3), md=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig4), md=12, className="mb-3"),
        ]),
    ])
