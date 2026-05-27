"""Tab: Mapa Provincial — distribución geográfica de captaciones."""
import pathlib
import json
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html

DATA_DIR = pathlib.Path(__file__).parent.parent.parent.parent / "data" / "processed"

# URL primaria: GeoJSON propio en el repo (siempre disponible en producción)
GEOJSON_URL = (
    "https://raw.githubusercontent.com/ErickPerezOrtiz/SIF-Bancario-/main/"
    "data/geojson/provincias_rd.geojson"
)
# Fallback alternativo en caso de que el repo no esté accesible
GEOJSON_URL_FALLBACK = (
    "https://raw.githubusercontent.com/jeasoft/provinces_geojson/master/"
    "provinces_municipality_summary.geojson"
)
GEOJSON_DISK_CACHE = DATA_DIR / "provincias_rd.geojson"
_GEOJSON_MEM_CACHE: dict | None = None   # caché en memoria para evitar re-descargas

COLORS = {
    "azul_sb": "#003087",
    "rojo":    "#C8102E",
    "dorado":  "#F5A623",
    "verde":   "#28A745",
}

LOCALIDAD_MAP = {
    "Santo Domingo": "Distrito Nacional",
    "DN":            "Distrito Nacional",
    "SDO":           "Santo Domingo",
    "Santiago":      "Santiago",
    "La Vega":       "La Vega",
    "San Cristóbal": "San Cristóbal",
    "San Pedro":     "San Pedro de Macorís",
    "La Romana":     "La Romana",
    "Puerto Plata":  "Puerto Plata",
    "Duarte":        "Duarte",
    "Espaillat":     "Espaillat",
    "Azua":          "Azua",
    "Barahona":      "Barahona",
    "El Seibo":      "El Seibo",
    "Hato Mayor":    "Hato Mayor",
    "Peravia":       "Peravia",
    "San Juan":      "San Juan",
    "María Trinidad Sánchez": "María Trinidad Sánchez",
    "Monte Cristi":  "Montecristi",
    "Samaná":        "Samaná",
    "Sánchez Ramírez": "Sánchez Ramírez",
}

# Corrección ortográfica API (sin acentos) → GeoJSON (con acentos, en mayúsculas)
API_PROVINCE_FIXES = {
    "BAHORUCO":               "BAORUCO",
    "DAJABON":                "DAJABÓN",
    "SAN CRISTOBAL":          "SAN CRISTÓBAL",
    "SAMANA":                 "SAMANÁ",
    "SAN PEDRO DE MACORIS":   "SAN PEDRO DE MACORÍS",
    "SANCHEZ RAMIREZ":        "SÁNCHEZ RAMÍREZ",
    "SANTIAGO RODRIGUEZ":     "SANTIAGO RODRÍGUEZ",
    "SAN JOSE DE OCOA":       "SAN JOSÉ DE OCOA",
    "MARIA TRINIDAD SANCHEZ": "MARÍA TRINIDAD SÁNCHEZ",
    "MONSENOR NOUEL":         "MONSEÑOR NOUEL",
}


def _load_geojson() -> dict | None:
    global _GEOJSON_MEM_CACHE
    if _GEOJSON_MEM_CACHE is not None:
        return _GEOJSON_MEM_CACHE

    # 1. Disco local (runtime cache, gitignored)
    if GEOJSON_DISK_CACHE.exists():
        with open(GEOJSON_DISK_CACHE, encoding="utf-8") as f:
            _GEOJSON_MEM_CACHE = json.load(f)
            return _GEOJSON_MEM_CACHE

    # 2. URL propia en GitHub (fuente de verdad en producción)
    for url in (GEOJSON_URL, GEOJSON_URL_FALLBACK):
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                _GEOJSON_MEM_CACHE = r.json()
                # Guardar en disco para la vida del proceso
                GEOJSON_DISK_CACHE.parent.mkdir(parents=True, exist_ok=True)
                with open(GEOJSON_DISK_CACHE, "w", encoding="utf-8") as f:
                    json.dump(_GEOJSON_MEM_CACHE, f)
                return _GEOJSON_MEM_CACHE
        except Exception:
            continue
    return None


def _captaciones_por_provincia(az) -> pd.DataFrame:
    try:
        df = az.captaciones_por_localidad()
        if df.empty:
            return pd.DataFrame()
        # LOCALIDAD_MAP handles old CSV-style names; API uppercase names fall through as-is
        df["provincia"] = df["localidad"].map(lambda x: LOCALIDAD_MAP.get(x, x))
        result = (
            df.groupby("provincia")["total_captado"]
            .sum().reset_index()
            .rename(columns={"total_captado": "captado"})
        )
        # provincia_key (uppercase) debe coincidir con properties.province_name del GeoJSON
        result["provincia_key"] = result["provincia"].str.upper()
        # Corregir diferencias API (sin acentos/errores) → GeoJSON (con acentos)
        result["provincia_key"] = result["provincia_key"].replace(API_PROVINCE_FIXES)
        # Fusionar Distrito Nacional en la provincia Santo Domingo (Gran Santo Domingo)
        result["provincia_key"] = result["provincia_key"].replace(
            "DISTRITO NACIONAL", "SANTO DOMINGO"
        )
        # Re-agregar después de la fusión (por si había dos filas)
        result = result.groupby("provincia_key", as_index=False)["captado"].sum()
        # Nombre para display con title-case
        result["provincia"] = result["provincia_key"].str.title()
        return result
    except Exception:
        return pd.DataFrame()


def _info_panel():
    return dbc.Card([dbc.CardBody([
        html.H6("Guía de interpretación — Mapa Provincial",
                style={"color": COLORS["azul_sb"], "fontWeight": "700", "marginBottom": "8px"}),
        dbc.Row([
            dbc.Col([
                html.P([html.Strong("¿Qué revela la concentración DN/Santiago? "),
                        "El Distrito Nacional y Santiago concentran más del 75% de las "
                        "captaciones del sistema bancario dominicano. Esto refleja la "
                        "distribución del PIB y la población urbana, pero también indica "
                        "una marcada exclusión financiera en el resto del país, "
                        "especialmente en zonas rurales y fronterizas."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("¿Qué significa para la inclusión financiera? "),
                        "Las provincias con menor captación per cápita tienen mayor "
                        "dependencia de efectivo, menor acceso a crédito formal y mayor "
                        "vulnerabilidad ante shocks económicos. La concentración bancaria "
                        "geográfica es un indicador estructural de desigualdad financiera."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
            dbc.Col([
                html.P([html.Strong("Provincias con mayor potencial de crecimiento: "),
                        "San Pedro de Macorís, La Romana y Puerto Plata tienen actividad "
                        "turística e industrial significativa pero baja penetración bancaria. "
                        "La Vega y Duarte son centros agropecuarios con oportunidades "
                        "claras para el microcrédito rural y la banca digital."],
                       style={"fontSize": "0.87rem", "marginBottom": "8px"}),
                html.P([html.Strong("Cómo leer el mapa: "),
                        "Los colores más oscuros (azul intenso) indican mayor volumen de "
                        "captaciones acumulado 2015-2025. El choropleth usa el GeoJSON "
                        "oficial de provincias dominicanas. Pasa el cursor sobre cada "
                        "provincia para ver el monto exacto."],
                       style={"fontSize": "0.87rem", "marginBottom": "0"}),
            ], md=6),
        ]),
    ])], style={"backgroundColor": "#EBF3FB", "borderLeft": f"4px solid {COLORS['azul_sb']}",
                "borderRadius": "6px", "border": "1px solid #D0E4F5"},
       className="mb-3")


def render(az) -> html.Div:
    geojson  = _load_geojson()
    df_prov  = _captaciones_por_provincia(az)

    if geojson is None or df_prov.empty:
        fig_mapa = go.Figure()
        fig_mapa.add_annotation(
            text="GeoJSON no disponible — revisa conexión a internet o datos vacíos",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font={"size": 13, "color": "gray"}
        )
        fig_mapa.update_layout(title="Distribución Geográfica de Captaciones", height=500)
    else:
        fig_mapa = px.choropleth(
            df_prov,
            geojson=geojson,
            locations="provincia_key",
            featureidkey="properties.province_name",
            color="captado",
            hover_name="provincia",
            color_continuous_scale="Blues",
            title="Captaciones por Provincia — Acumulado 2015-2025 (RD$)",
            labels={"captado": "Captado (RD$)"},
        )
        fig_mapa.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>Captado (RD$): %{z:,.0f}<extra></extra>"
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False,
                             projection_type="mercator")
        fig_mapa.update_layout(
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            height=550,
            coloraxis_colorbar={"title": "RD$"},
        )

    # Bar chart complementario
    fig_bar = go.Figure()
    if not df_prov.empty:
        df_sorted = df_prov.sort_values("captado", ascending=True).copy()
        fig_bar.add_trace(go.Bar(
            x=df_sorted["captado"],
            y=df_sorted["provincia"],
            orientation="h",
            marker_color=COLORS["azul_sb"],
        ))
    fig_bar.update_layout(
        title="Captaciones por Provincia — Vista de Barras",
        xaxis_title="Total Captado (RD$)",
        plot_bgcolor="white", paper_bgcolor="white",
        height=500,
    )

    # Tabla resumen con % acumulado
    tabla_rows = []
    if not df_prov.empty:
        total = df_prov["captado"].sum()
        df_sorted_desc = df_prov.sort_values("captado", ascending=False).reset_index(drop=True)
        acum = 0.0
        for _, row in df_sorted_desc.iterrows():
            pct = row["captado"] / total * 100
            acum += pct
            tabla_rows.append(html.Tr([
                html.Td(row["provincia"]),
                html.Td(f"RD$ {row['captado']/1_000:,.1f} mil MM"),
                html.Td(f"{pct:.1f}%"),
                html.Td(f"{acum:.1f}%",
                        style={"color": COLORS["rojo"] if acum > 75 else COLORS["verde"],
                               "fontWeight": "600"}),
            ]))

    return html.Div([
        _info_panel(),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_mapa), md=7, className="mb-3"),
            dbc.Col(dcc.Graph(figure=fig_bar),  md=5, className="mb-3"),
        ]),
        html.H5("Resumen por Provincia",
                className="mb-2", style={"color": COLORS["azul_sb"]}),
        dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Provincia"), html.Th("Total Captado"),
                    html.Th("% del Total"), html.Th("% Acumulado"),
                ])),
                html.Tbody(tabla_rows),
            ],
            bordered=True, hover=True, striped=True, className="table-sm"
        ) if tabla_rows else dbc.Alert("Sin datos provinciales disponibles.", color="info"),
    ])
