"""Tab: Conceptos — glosario financiero del sistema SIF-Bancario."""
import dash_bootstrap_components as dbc
from dash import html

COLORS = {
    "azul_sb":  "#003087",
    "verde":    "#28A745",
    "naranja":  "#E67E22",
    "rojo":     "#C8102E",
    "morado":   "#6C3483",
    "bg_light": "#F8F9FA",
}

# Color por sección
SEC_COLORS = {
    1: COLORS["azul_sb"],
    2: COLORS["verde"],
    3: COLORS["naranja"],
    4: COLORS["rojo"],
    5: COLORS["morado"],
}

SEC_BG = {
    1: "#EBF3FB",
    2: "#EAFAF1",
    3: "#FEF5E7",
    4: "#FDEDEC",
    5: "#F4ECF7",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _concepto_card(nombre, definicion, ejemplo, seccion):
    color = SEC_COLORS[seccion]
    bg    = SEC_BG[seccion]
    return dbc.Card([
        dbc.CardBody([
            html.P(
                html.Strong(nombre),
                style={"color": color, "fontWeight": "700",
                       "marginBottom": "4px", "fontSize": "0.95rem"},
                className="mb-1"
            ),
            html.P(definicion,
                   style={"fontSize": "0.87rem", "color": "#333", "marginBottom": "4px"},
                   className="mb-1"),
            html.P(
                html.I(f"Ejemplo: {ejemplo}"),
                style={"fontSize": "0.82rem", "color": "#777"},
                className="mb-0"
            ),
        ])
    ], style={
        "borderLeft": f"4px solid {color}",
        "backgroundColor": bg,
        "borderRadius": "6px",
        "border": f"1px solid {color}30",
    }, className="shadow-sm mb-2 h-100")


def _seccion_header(numero, titulo, color):
    return html.Div([
        html.H5([
            html.Span(f"Sección {numero} — ",
                      style={"color": color, "fontWeight": "800"}),
            titulo,
        ], style={"color": color, "fontWeight": "700",
                  "borderBottom": f"2px solid {color}",
                  "paddingBottom": "6px", "marginBottom": "16px"}),
    ], className="mt-4 mb-3")


# ── Datos de conceptos ────────────────────────────────────────────────────────

CAPTACIONES = [
    (
        "Captaciones",
        "Fondos que el público (personas, empresas, gobierno) deposita en el sistema bancario. "
        "Son la principal fuente de financiamiento de los bancos para otorgar préstamos.",
        "El Banco Popular capta depósitos de sus clientes al 4% anual y los presta a empresas al 12%."
    ),
    (
        "Depósito a la vista",
        "Depósito disponible para retiro en cualquier momento sin previo aviso. "
        "Incluye cuentas corrientes y de cheques. Generalmente ofrece tasas bajas o nulas.",
        "Una empresa mantiene RD$ 2 millones en cuenta corriente para cubrir nómina diaria."
    ),
    (
        "Depósito a plazo",
        "Depósito que el cliente acuerda mantener por un período fijo (30, 60, 90, 180 o 360 días). "
        "A cambio, recibe una tasa de interés más alta que la cuenta de ahorro.",
        "Una familia coloca RD$ 500,000 a 180 días al 7% anual en un banco múltiple dominicano."
    ),
    (
        "Cuenta de ahorro",
        "Depósito de libre disponibilidad pero diseñado para acumular fondos a mediano plazo. "
        "Genera intereses más bajos que un depósito a plazo, pero mayores que la cuenta corriente.",
        "Un trabajador deposita parte de su sueldo mensual en una cuenta de ahorro en Asociación Popular."
    ),
    (
        "Dolarización de depósitos",
        "Proporción de los depósitos del sistema bancario que se mantienen en moneda extranjera (USD). "
        "Un nivel alto puede indicar desconfianza en la moneda local o presencia de sectores exportadores.",
        "Si el 28% de las captaciones del sistema están en USD, el sistema tiene un nivel de dolarización del 28%."
    ),
    (
        "Tipo de depositante",
        "Clasificación del titular de la cuenta según su naturaleza jurídica: personas físicas, "
        "empresas privadas, gobierno central, instituciones financieras u organismos internacionales.",
        "Los hogares representan ~55% de las captaciones del sistema bancario dominicano."
    ),
]

CREDITO = [
    (
        "Cartera de créditos",
        "Conjunto de todos los préstamos otorgados por una institución financiera a sus clientes. "
        "Se clasifica según el riesgo de cobro: normal, subestándar, dudoso e irrecuperable.",
        "La cartera total del sistema bancario dominicano superó RD$ 1.2 billones en 2024."
    ),
    (
        "Cartera vigente",
        "Porción de la cartera de créditos que se encuentra al día en sus pagos, "
        "sin días de atraso o con atrasos menores a 30 días. También llamada cartera normal.",
        "Un banco con 97% de cartera vigente tiene solo el 3% de sus préstamos con problemas de pago."
    ),
    (
        "Cartera vencida",
        "Créditos que acumulan más de 30 días de atraso en el pago de capital o intereses. "
        "Requiere que el banco constituya provisiones para cubrir la posible pérdida.",
        "Un crédito hipotecario que lleva 45 días sin pago pasa a clasificarse como cartera vencida."
    ),
    (
        "Índice de morosidad",
        "Razón entre la cartera vencida y la cartera total. Mide el porcentaje de préstamos "
        "en riesgo de no ser cobrados. La Superintendencia de Bancos de RD monitorea este indicador mensualmente.",
        "Si un banco tiene RD$ 50 MM en mora y RD$ 2,000 MM en cartera total, su índice es 2.5%."
    ),
    (
        "Morosidad estresada",
        "Medida ampliada de riesgo crediticio que incluye cartera reestructurada, refinanciada "
        "y créditos con atraso de 1-30 días, además de la cartera vencida clásica.",
        "Durante COVID-2020, la morosidad estresada del sistema dominicano superó el 8%, aunque la clásica fue 2.5%."
    ),
    (
        "Provisiones",
        "Reservas de capital que los bancos deben apartar para cubrir pérdidas esperadas en la cartera. "
        "La normativa de la SB establece porcentajes mínimos según la clasificación de riesgo del crédito.",
        "Un crédito clasificado como 'dudoso' requiere constituir al menos el 50% de su saldo en provisiones."
    ),
    (
        "Crédito comercial",
        "Financiamiento otorgado a empresas para capital de trabajo, adquisición de equipos "
        "o expansión del negocio. Generalmente tiene montos mayores y plazos más cortos que el crédito de consumo.",
        "Una empresa constructora obtiene una línea de crédito comercial de RD$ 10 MM para comprar materiales."
    ),
    (
        "Crédito de consumo",
        "Préstamo otorgado a personas físicas para fines personales: compra de electrodomésticos, "
        "vehículos, viajes o gastos imprevistos. Suele tener tasas más altas que el crédito hipotecario.",
        "Un empleado obtiene un préstamo personal de RD$ 200,000 a 24 meses para renovar su hogar."
    ),
    (
        "Crédito hipotecario",
        "Préstamo garantizado con un bien inmueble (casa, apartamento, terreno). "
        "Tiene los plazos más largos del sistema (hasta 25-30 años) y las tasas más bajas por la garantía real.",
        "Una familia toma un préstamo hipotecario de RD$ 4 millones a 20 años para comprar su primer hogar."
    ),
    (
        "Sector económico",
        "Clasificación de los prestatarios según la actividad productiva a la que destinan el crédito: "
        "agropecuario, comercio, industria, turismo, construcción, consumo, entre otros.",
        "El sector turismo concentra el 12% de la cartera de créditos comerciales en la banca dominicana."
    ),
]

INDICADORES = [
    (
        "Solvencia",
        "Capacidad de una institución financiera para cumplir con sus obligaciones a largo plazo "
        "con su propio capital. Un banco solvente puede absorber pérdidas inesperadas sin quebrar.",
        "Un banco con índice de solvencia del 15% tiene colchón suficiente para absorber una crisis moderada."
    ),
    (
        "Índice de adecuación de capital (IAC)",
        "Ratio entre el capital regulatorio y los activos ponderados por riesgo (APR). "
        "La Ley Monetaria de la República Dominicana exige un mínimo del 10%.",
        "Si un banco tiene RD$ 15,000 MM de capital y RD$ 100,000 MM en APR, su IAC es 15%."
    ),
    (
        "Tier 1 — Capital Primario",
        "Capital de mayor calidad: acciones ordinarias emitidas y pagadas, más las reservas retenidas de utilidades. "
        "Es la primera línea de defensa ante pérdidas según los estándares de Basilea III.",
        "El capital Tier 1 del BPD incluye su capital social emitido más las utilidades acumuladas no distribuidas."
    ),
    (
        "Tier 2 — Capital Secundario",
        "Capital de menor calidad que el Tier 1: incluye deuda subordinada, reservas genéricas "
        "y otros instrumentos híbridos. Tiene un rol complementario en la absorción de pérdidas.",
        "Un banco emite bonos subordinados a 10 años que computan como capital Tier 2 hasta el 50% del Tier 1."
    ),
    (
        "Activos ponderados por riesgo (APR)",
        "Valor de los activos de un banco ajustado por su riesgo de crédito. Cada tipo de activo "
        "recibe una ponderación: 0% para bonos soberanos, 100% para préstamos comerciales sin garantía.",
        "Una cartera de hipotecas residenciales pondera al 35%, mientras que un préstamo comercial pondera al 100%."
    ),
    (
        "Liquidez inmediata",
        "Porcentaje de los depósitos que el banco mantiene en activos líquidos de alta calidad "
        "(efectivo, encaje en el BCRD, bonos del Ministerio de Hacienda). La SB exige un mínimo del 15%.",
        "Si un banco tiene RD$ 30,000 MM en activos líquidos y RD$ 100,000 MM en depósitos, su liquidez es 30%."
    ),
    (
        "ROA — Retorno sobre activos",
        "Beneficio neto dividido entre activos totales. Mide qué tan eficientemente usa el banco "
        "sus activos para generar ganancias. Un ROA > 1.5% es considerado saludable en RD.",
        "Un banco con utilidades de RD$ 3,000 MM y activos de RD$ 200,000 MM tiene un ROA de 1.5%."
    ),
    (
        "ROE — Retorno sobre patrimonio",
        "Beneficio neto dividido entre el capital propio. Mide el retorno que reciben los accionistas "
        "por su inversión. Un ROE > 12% es competitivo en el sistema bancario dominicano.",
        "Si el banco anterior tiene un patrimonio de RD$ 20,000 MM, su ROE es 15% (RD$ 3,000 / RD$ 20,000)."
    ),
    (
        "Eficiencia operacional",
        "Ratio entre los gastos operativos y los ingresos netos. Cuanto menor el valor, más eficiente "
        "es el banco. Un ratio menor al 55% se considera bueno en la banca regional.",
        "Un banco con RD$ 5,000 MM en gastos y RD$ 10,000 MM en ingresos tiene eficiencia del 50%."
    ),
    (
        "Spread de intermediación",
        "Diferencia entre la tasa activa (lo que cobran por préstamos) y la tasa pasiva "
        "(lo que pagan por depósitos). Es el margen de ganancia principal del negocio bancario.",
        "Si un banco presta al 14% y capta al 5%, su spread de intermediación es 9 puntos porcentuales."
    ),
]

MACRO = [
    (
        "Tasa de Política Monetaria (TPM)",
        "Tasa de interés de referencia que fija el Banco Central de la República Dominicana (BCRD) "
        "para regular el costo del dinero en la economía. Afecta directamente las tasas activas y pasivas del sistema bancario.",
        "Cuando el BCRD subió la TPM de 3% a 8.5% en 2022, los bancos encarecieron sus préstamos para controlar la inflación."
    ),
    (
        "Inflación",
        "Aumento generalizado y sostenido del nivel de precios de bienes y servicios en la economía. "
        "Una inflación alta erosiona el poder adquisitivo y puede deteriorar la calidad de la cartera crediticia.",
        "En 2022, la inflación interanual en RD alcanzó 9.64%, el nivel más alto desde 2004."
    ),
    (
        "IPC — Índice de Precios al Consumidor",
        "Indicador que mide la evolución del costo de una canasta representativa de bienes y servicios "
        "que consume un hogar promedio. Es el indicador oficial de inflación en República Dominicana.",
        "Si el IPC sube de 110 a 120 puntos en un año, la inflación anual fue del 9.09% en ese período."
    ),
    (
        "Tipo de cambio",
        "Precio de una moneda extranjera (USD) expresado en moneda local (DOP). "
        "Cuando sube, el peso se deprecia y los bienes importados se encarecen.",
        "El tipo de cambio pasó de RD$ 44.50 por dólar en 2015 a RD$ 61.50 en 2025, una depreciación del 38%."
    ),
    (
        "Depreciación cambiaria",
        "Pérdida de valor de la moneda local frente a una moneda de referencia como el USD. "
        "Afecta negativamente a quienes tienen deudas en dólares pero ingresos en pesos.",
        "Una empresa que importa insumos pagaderos en USD sufre mayor costo en pesos cuando el tipo de cambio sube."
    ),
    (
        "PIB — Producto Interno Bruto",
        "Valor total de todos los bienes y servicios producidos en un país durante un período determinado. "
        "Es el principal indicador del tamaño y dinamismo de la economía.",
        "En Q2-2020, el PIB de RD cayó -15.3% frente al mismo trimestre de 2019 por el impacto del COVID-19."
    ),
    (
        "Remesas",
        "Transferencias de dinero que los migrantes dominicanos en el exterior envían a sus familias en RD. "
        "Son el mayor componente de la balanza de pagos y un factor clave de la inclusión financiera.",
        "En 2021, las remesas hacia RD alcanzaron USD 10,431 millones, equivalente al ~10% del PIB nacional."
    ),
    (
        "Política monetaria contractiva",
        "Política del Banco Central que busca reducir la liquidez en la economía para bajar la inflación. "
        "Se instrumenta subiendo la TPM, el encaje legal o vendiendo valores del banco central.",
        "La subida de TPM de 550 pb entre 2022 y 2023 fue una política monetaria contractiva para frenar la inflación."
    ),
    (
        "Política monetaria expansiva",
        "Política del Banco Central que busca estimular la economía inyectando liquidez. "
        "Se instrumenta bajando la TPM, el encaje legal o comprando valores en el mercado.",
        "En 2020, el BCRD bajó la TPM 300 pb y liberó el encaje para inyectar liquidez durante la pandemia."
    ),
]

ESTADISTICA = [
    (
        "Media (promedio)",
        "Suma de todos los valores dividida entre el número de observaciones. "
        "Es el indicador de tendencia central más común, pero sensible a valores extremos (outliers).",
        "Si 5 bancos tienen captaciones de RD$ 100, 200, 150, 300 y 250 MM, la media es RD$ 200 MM."
    ),
    (
        "Desviación estándar",
        "Medida de dispersión que indica cuánto se alejan los valores individuales de la media. "
        "Una desviación alta implica mayor variabilidad en los datos.",
        "Si la desviación estándar de captaciones es muy alta, hay grandes diferencias entre bancos grandes y pequeños."
    ),
    (
        "Skewness — Asimetría",
        "Medida de la asimetría de una distribución respecto a la media. Un skewness positivo (sesgado a la derecha) "
        "indica que hay valores extremadamente altos; uno negativo indica valores extremadamente bajos.",
        "Las captaciones del sistema tienen skewness ≈ 3.28: pocos bancos gigantes concentran montos enormes."
    ),
    (
        "Kurtosis",
        "Medida de la 'altura' y 'peso' de las colas de una distribución comparada con la distribución normal. "
        "Una kurtosis > 3 (leptocúrtica) indica colas pesadas con más valores extremos de lo esperado.",
        "Los datos financieros suelen tener kurtosis alta porque los shocks de mercado generan valores extremos."
    ),
    (
        "Percentil",
        "Valor por debajo del cual cae un porcentaje determinado de las observaciones. "
        "El percentil 75 (Q3) indica que el 75% de los datos son menores a ese valor.",
        "Si el percentil 90 de captaciones es RD$ 500 MM, el 90% de los registros están por debajo de ese monto."
    ),
    (
        "Correlación de Pearson (r)",
        "Medida de la relación lineal entre dos variables continuas. Va de -1 (correlación negativa perfecta) "
        "a +1 (correlación positiva perfecta). Un valor de 0 indica ausencia de correlación lineal.",
        "La correlación remesas-captaciones de r = 0.84 indica que ambas variables se mueven juntas con fuerza."
    ),
    (
        "Regresión OLS — Mínimos Cuadrados Ordinarios",
        "Método estadístico que estima la relación lineal entre una variable dependiente (ej. morosidad) "
        "y una o más variables independientes (TPM, IPC, tipo de cambio). Minimiza los errores cuadráticos.",
        "El modelo OLS del tab Stress Testing estima cómo cambia la morosidad cuando sube la TPM en 1 punto."
    ),
    (
        "R² — Coeficiente de determinación",
        "Porcentaje de la variación en la variable dependiente que es explicado por el modelo. "
        "Va de 0 a 1 (equivalente a 0%-100%). Un R² > 0.60 es bueno para datos macroeconómicos.",
        "Si el modelo OLS tiene R² = 0.75, el 75% de los cambios en morosidad son explicados por TPM, IPC y TC."
    ),
    (
        "Intervalo de confianza 95%",
        "Rango de valores dentro del cual, con 95% de probabilidad, cae el valor real del parámetro estimado. "
        "Un intervalo estrecho indica mayor precisión del modelo.",
        "Si la morosidad proyectada es 2.5% con IC [1.8%, 3.2%], el valor real estará en ese rango el 95% del tiempo."
    ),
    (
        "Outlier — Valor atípico",
        "Observación que se aleja significativamente del patrón general de los datos. "
        "Puede ser un error de medición o un evento real extraordinario. Se detecta con IQR o Z-score > 3.",
        "Un banco que capta RD$ 50,000 MM en un mes —10 veces más que lo habitual— sería un outlier estadístico."
    ),
]


# ── Render ────────────────────────────────────────────────────────────────────

def render() -> html.Div:
    def seccion(num, titulo, conceptos_list):
        color = SEC_COLORS[num]
        return html.Div([
            _seccion_header(num, titulo, color),
            dbc.Row([
                dbc.Col([_concepto_card(n, d, e, num)], md=6)
                for n, d, e in conceptos_list
            ], className="g-2 mb-2"),
        ])

    return html.Div([
        # Panel introductorio
        dbc.Card([dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5("Glosario Financiero — SIF-Bancario",
                            style={"color": COLORS["azul_sb"], "fontWeight": "700",
                                   "marginBottom": "8px"}),
                    html.P(
                        "Este glosario define los términos clave necesarios para interpretar "
                        "correctamente los gráficos, indicadores y análisis del dashboard. "
                        "Los conceptos se presentan en lenguaje claro, con ejemplos aplicados "
                        "a la realidad bancaria de la República Dominicana.",
                        style={"fontSize": "0.9rem", "color": "#444", "marginBottom": "8px"}
                    ),
                    html.P(
                        "Cada sección agrupa conceptos relacionados por tema: captaciones, crédito, "
                        "indicadores prudenciales, macroeconomía y estadística.",
                        style={"fontSize": "0.9rem", "color": "#444", "marginBottom": "0"}
                    ),
                ], md=8),
                dbc.Col([
                    html.Div([
                        dbc.Badge("5 secciones temáticas",  color="primary",   className="me-2 mb-2 d-block"),
                        dbc.Badge("40 conceptos definidos", color="success",   className="me-2 mb-2 d-block"),
                        dbc.Badge("Con ejemplos de RD",     color="warning",   className="me-2 mb-2 d-block"),
                    ], className="d-flex flex-column align-items-start pt-2"),
                ], md=4),
            ])
        ])], style={"borderLeft": f"4px solid {COLORS['azul_sb']}", "backgroundColor": "#EBF3FB",
                    "border": "1px solid #D0E4F5", "borderRadius": "6px"},
            className="shadow-sm mb-4"),

        # Índice de secciones
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.P("Índice de secciones:",
                           className="fw-bold mb-2",
                           style={"color": COLORS["azul_sb"], "fontSize": "0.9rem"}),
                    html.Div([
                        html.Span(
                            f"  {i+1}. {titulo}",
                            style={"backgroundColor": color,
                                   "color": "white",
                                   "padding": "3px 12px",
                                   "borderRadius": "12px",
                                   "fontSize": "0.8rem",
                                   "display": "inline-block",
                                   "marginRight": "8px",
                                   "marginBottom": "6px"}
                        )
                        for i, (titulo, color) in enumerate([
                            ("Captaciones",               COLORS["azul_sb"]),
                            ("Crédito",                   COLORS["verde"]),
                            ("Indicadores Prudenciales",  COLORS["naranja"]),
                            ("Macroeconomía",             COLORS["rojo"]),
                            ("Estadística y Análisis",    COLORS["morado"]),
                        ])
                    ])
                ])], className="shadow-sm"),
            ])
        ], className="mb-4"),

        # Secciones temáticas
        seccion(1, "Captaciones",              CAPTACIONES),
        seccion(2, "Crédito",                  CREDITO),
        seccion(3, "Indicadores Prudenciales", INDICADORES),
        seccion(4, "Macroeconomía y Política Monetaria", MACRO),
        seccion(5, "Estadística y Análisis",   ESTADISTICA),

        html.Hr(className="mt-4"),
        html.P(
            "Fuentes de referencia: Ley Monetaria y Financiera de la República Dominicana, "
            "Reglamentos de la Superintendencia de Bancos, Banco Central de la República Dominicana (BCRD), "
            "Acuerdos de Basilea III, Fondo Monetario Internacional (FMI).",
            className="text-muted text-center",
            style={"fontSize": "0.8rem", "paddingBottom": "12px"}
        ),
    ])
