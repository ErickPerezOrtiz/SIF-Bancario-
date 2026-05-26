"""Tab: Stress Testing — simulación OLS con sliders interactivos."""
import pathlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

DATA_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "data" / "processed"

COLORS = {
    "azul_sb": "#003087",
    "rojo":    "#C8102E",
    "dorado":  "#F5A623",
    "verde":   "#28A745",
}


def _info_panel():
    return dbc.Card([dbc.CardBody([
        html.H6("Guía de interpretación — Stress Testing OLS",
                style={"color": COLORS["azul_sb"], "fontWeight": "700", "marginBottom": "8px"}),
        dbc.Row([
            dbc.Col([
                html.P([html.Strong("¿Qué es un modelo OLS? "),
                        "OLS (Ordinary Least Squares, Mínimos Cuadrados Ordinarios) es una "
                        "regresión lineal que estima el efecto de cada variable macroeconómica "
                        "(TPM, IPC, TC) sobre el índice de morosidad. El modelo minimiza la "
                        "suma de los errores cuadráticos para encontrar los coeficientes más "
                        "precisos."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Qué es R² y cómo se interpreta? "),
                        "El R² (coeficiente de determinación) mide qué porcentaje de la "
                        "variación en la morosidad explican las variables macro. Un R² de 0.75 "
                        "significa que el 75% de los cambios en morosidad son explicados por "
                        "TPM, inflación y tipo de cambio. Un R² > 0.60 se considera bueno "
                        "para datos macroeconómicos."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
            dbc.Col([
                html.P([html.Strong("¿Cómo usar los sliders? "),
                        "Los tres sliders representan escenarios hipotéticos: sube la TPM "
                        "para simular una política monetaria restrictiva, aumenta el IPC para "
                        "simular un shock inflacionario, o ajusta el tipo de cambio para "
                        "simular una devaluación. El modelo predice el índice de morosidad "
                        "esperado bajo ese escenario."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Qué significa el intervalo de confianza 95%? "),
                        "El IC 95% es el rango dentro del cual la morosidad real caerá "
                        "el 95% del tiempo bajo ese escenario. Un intervalo amplio indica "
                        "mayor incertidumbre. Si el límite superior del IC supera el 4%, "
                        "el escenario es de riesgo alto aunque el valor central sea menor."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
        ]),
    ])], style={"backgroundColor": "#EBF3FB", "borderLeft": f"4px solid {COLORS['azul_sb']}",
                "borderRadius": "6px", "border": "1px solid #D0E4F5"},
       className="mb-3")


def _build_regression_data():
    try:
        import statsmodels.api as sm

        p_tpm = DATA_DIR / "macro_tasas.csv"
        p_ipc = DATA_DIR / "macro_inflacion.csv"
        p_tc  = DATA_DIR / "macro_tipo_cambio.csv"
        p_car = DATA_DIR / "cartera_creditos.csv"

        if not all(p.exists() for p in [p_tpm, p_ipc, p_tc]):
            return pd.DataFrame(), None

        df_tpm = pd.read_csv(p_tpm, parse_dates=["fecha"])
        df_ipc = pd.read_csv(p_ipc, parse_dates=["fecha"])
        df_tc  = pd.read_csv(p_tc,  parse_dates=["fecha"])

        df = (
            df_tpm[["fecha", "tpm_nominal"]]
            .merge(df_ipc[["fecha", "ipc_interanual_pct"]], on="fecha")
            .merge(df_tc[["fecha",  "venta_dop_usd"]],      on="fecha")
        )

        if p_car.exists():
            df_car = pd.read_csv(p_car, parse_dates=["fecha"])
            df_car["periodo"] = df_car["fecha"].dt.to_period("M").dt.to_timestamp()
            car_g = df_car.groupby("periodo").agg(
                normal=("clasificacion_riesgo",
                        lambda x: (x == "Normal").sum()),
                total=("clasificacion_riesgo", "count"),
            ).reset_index()
            car_g["morosidad"] = (1 - car_g["normal"] / car_g["total"]) * 100
            car_g = car_g.rename(columns={"periodo": "fecha"})
            df = df.merge(car_g[["fecha","morosidad"]], on="fecha", how="left")
        else:
            df["morosidad"] = 3.0 + np.random.default_rng(42).normal(0, 0.3, len(df))

        df = df.dropna()
        X = sm.add_constant(df[["tpm_nominal","ipc_interanual_pct","venta_dop_usd"]])
        y = df["morosidad"]
        results = sm.OLS(y, X).fit()
        return df, results

    except Exception:
        return pd.DataFrame(), None


def render(az) -> html.Div:
    df, results = _build_regression_data()

    # Panel de modelo
    if results is not None:
        r2     = results.rsquared
        params = results.params
        bse    = results.bse

        r2_color = "success" if r2 > 0.6 else ("warning" if r2 > 0.4 else "danger")

        model_info = dbc.Card([
            dbc.CardHeader(
                "Modelo OLS — Variable dependiente: Índice de Morosidad (%)",
                style={"backgroundColor": COLORS["azul_sb"], "color": "white",
                       "fontWeight": "bold"}
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Alert([
                            html.H5(f"R² = {r2:.4f}", className="alert-heading mb-1"),
                            html.Small(
                                f"{'Excelente' if r2>0.75 else 'Bueno' if r2>0.60 else 'Aceptable'} "
                                f"— el modelo explica el {r2*100:.1f}% de la variación en morosidad",
                                style={"fontSize": "0.82rem"}
                            ),
                        ], color=r2_color, className="mb-2"),
                        html.P(f"R² ajustado: {results.rsquared_adj:.4f}", className="mb-1",
                               style={"fontSize": "0.9rem"}),
                        html.P(f"N observaciones: {int(results.nobs)}", className="mb-1",
                               style={"fontSize": "0.9rem"}),
                        html.P(f"F-statistic: {results.fvalue:.2f} (p={results.f_pvalue:.4f})",
                               className="mb-0", style={"fontSize": "0.9rem"}),
                    ], md=4),
                    dbc.Col([
                        dbc.Table(
                            [html.Thead(html.Tr([
                                html.Th("Variable"), html.Th("Coeficiente"),
                                html.Th("Std. Error"), html.Th("p-valor"),
                            ]))] +
                            [html.Tbody([
                                html.Tr([
                                    html.Td(k, style={"fontSize": "0.85rem"}),
                                    html.Td(f"{params[k]:.4f}", style={"fontSize": "0.85rem"}),
                                    html.Td(f"{bse[k]:.4f}",    style={"fontSize": "0.85rem"}),
                                    html.Td(f"{results.pvalues[k]:.4f}",
                                            style={"color": COLORS["verde"]
                                                   if results.pvalues[k] < 0.05
                                                   else COLORS["rojo"],
                                                   "fontSize": "0.85rem", "fontWeight": "600"}),
                                ])
                                for k in params.index
                            ])],
                            bordered=True, striped=True, hover=True,
                            className="table-sm mb-0"
                        ),
                    ], md=8),
                ]),
            ]),
        ], className="shadow-sm mb-4")
    else:
        model_info = dbc.Alert(
            "No se pudo ajustar el modelo OLS. Asegúrate de haber generado los datos "
            "macro y bancarios (python seed_data.py y generar_macro_completo).",
            color="warning"
        )

    sliders = dbc.Card([
        dbc.CardHeader("Simulador de Escenarios — Ajusta los parámetros macro y observa el impacto",
                       style={"fontWeight": "bold"}),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Tasa de Política Monetaria — TPM (%)",
                               style={"fontWeight": "600", "fontSize": "0.9rem"}),
                    dcc.Slider(
                        id="stress-tpm", min=1.0, max=12.0, step=0.25,
                        value=6.75, marks={i: f"{i}%" for i in range(1, 13)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], md=12, className="mb-3"),
                dbc.Col([
                    html.Label("Inflación IPC Interanual (%)",
                               style={"fontWeight": "600", "fontSize": "0.9rem"}),
                    dcc.Slider(
                        id="stress-ipc", min=0.0, max=15.0, step=0.25,
                        value=4.0, marks={i: f"{i}%" for i in range(0, 16, 3)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], md=12, className="mb-3"),
                dbc.Col([
                    html.Label("Tipo de Cambio DOP/USD",
                               style={"fontWeight": "600", "fontSize": "0.9rem"}),
                    dcc.Slider(
                        id="stress-tc", min=50.0, max=90.0, step=0.5,
                        value=60.5, marks={i: f"{i}" for i in range(50, 91, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], md=12, className="mb-3"),
            ]),
            html.Div(id="stress-resultado", className="mt-2"),
        ]),
    ], className="shadow-sm mb-4")

    # Residuos
    fig_res = go.Figure()
    if results is not None and not df.empty:
        fig_res.add_trace(go.Scatter(
            x=results.fittedvalues, y=results.resid, mode="markers",
            marker={"color": COLORS["azul_sb"], "size": 5, "opacity": 0.6},
            name="Residuos"
        ))
        fig_res.add_hline(y=0, line_dash="dash", line_color=COLORS["rojo"])
    fig_res.update_layout(
        title="Residuos vs Valores Ajustados",
        xaxis_title="Valores Ajustados", yaxis_title="Residuos",
        plot_bgcolor="white", paper_bgcolor="white"
    )

    # QQ Plot
    fig_qq = go.Figure()
    if results is not None:
        try:
            from scipy import stats as scipy_stats
            resid_std = (results.resid - results.resid.mean()) / results.resid.std()
            qq = scipy_stats.probplot(resid_std, dist="norm")
            fig_qq.add_trace(go.Scatter(
                x=qq[0][0], y=qq[0][1], mode="markers",
                marker={"color": COLORS["azul_sb"], "size": 5},
                name="Quantiles"
            ))
            x_line = np.array([qq[0][0].min(), qq[0][0].max()])
            fig_qq.add_trace(go.Scatter(
                x=x_line, y=qq[1][1] + qq[1][0] * x_line,
                mode="lines", name="Normal teórica",
                line={"color": COLORS["rojo"], "dash": "dash"}
            ))
        except Exception:
            pass
    fig_qq.update_layout(
        title="Q-Q Plot de Residuos",
        xaxis_title="Cuantiles teóricos", yaxis_title="Cuantiles muestrales",
        plot_bgcolor="white", paper_bgcolor="white"
    )

    return html.Div([
        _info_panel(),
        model_info,
        sliders,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_res), md=6, className="mb-3"),
            dbc.Col(dcc.Graph(figure=fig_qq),  md=6, className="mb-3"),
        ]),
    ])


def register_stress_callback(app, az):
    import statsmodels.api as sm

    @app.callback(
        Output("stress-resultado", "children"),
        [Input("stress-tpm", "value"),
         Input("stress-ipc", "value"),
         Input("stress-tc",  "value")],
    )
    def actualizar_stress(tpm, ipc, tc):
        df, results = _build_regression_data()
        if results is None:
            return dbc.Alert("Modelo no disponible.", color="warning")

        X_new = sm.add_constant(
            pd.DataFrame([[tpm, ipc, tc]],
                         columns=["tpm_nominal","ipc_interanual_pct","venta_dop_usd"]),
            has_constant="add"
        )
        pred = results.predict(X_new)[0]
        ci   = results.get_prediction(X_new).conf_int(alpha=0.05)[0]

        color = "danger"  if pred > 5.0 else "warning" if pred > 3.0 else "success"
        nivel = "ALTO RIESGO" if pred > 5.0 else "RIESGO MODERADO" if pred > 3.0 else "RIESGO BAJO"

        return dbc.Alert([
            html.H4(f"Morosidad proyectada: {pred:.2f}%", className="alert-heading"),
            html.P(f"Intervalo de confianza 95%: [{ci[0]:.2f}%, {ci[1]:.2f}%]",
                   className="mb-1"),
            html.Hr(),
            html.P(f"Escenario: TPM = {tpm}% | IPC = {ipc}% | TC = {tc} DOP/USD",
                   className="mb-1 text-muted", style={"fontSize": "0.9rem"}),
            html.Span(nivel, style={
                "fontWeight": "bold", "fontSize": "1rem",
                "color": "#C8102E" if color == "danger" else
                         "#F5A623" if color == "warning" else "#28A745"
            }),
        ], color=color)
