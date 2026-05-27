# SIF — Banca Dominicana

**Sistema de Inteligencia Financiera · Portafolio · Erick Pérez · ITLA, Santo Domingo RD**

Dashboard interactivo de análisis del sistema bancario dominicano, con datos reales de la API pública de la **Superintendencia de Bancos de la República Dominicana** (2015-2025).

🔗 **Demo live:** [sif-bancario.onrender.com](https://sif-bancario.onrender.com)

---

## KPIs del sistema (datos reales)

| Indicador | Valor |
|---|---|
| Total Captado (DOP) | **RD$ 112.02 billones** |
| Cartera de Créditos | **RD$ 105.17 billones** |
| Entidades Supervisadas | **21** bancos múltiples |
| Períodos Disponibles | **132 meses** (2015-01 → 2025-12) |

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Dashboard | Plotly Dash 2.17 + Dash Bootstrap Components 1.6 |
| Análisis | pandas 2.2, numpy 1.24+, scipy 1.10+, statsmodels 0.14 |
| API | Superintendencia de Bancos RD (Azure APIM v2) |
| Datos | CSVs pre-generados desde API v2 SB (267,300 registros) |
| Base de datos | MySQL 8 via SQLAlchemy 2.0 (opcional, fallback a CSV) |
| Mapas | GeoJSON provincias RD + Plotly Choropleth |
| Deploy | Render.com (Free tier) |

---

## Fuente de datos

Los datos provienen de la **API v2 pública** de la Superintendencia de Bancos RD, pre-generados con `scripts/generar_datos.py` y almacenados como CSVs estáticos:

| Endpoint | Descripción |
|---|---|
| `indicadores/financieros` | ROE, apalancamiento, margen de intermediación, activos improductivos |
| `indicadores/principales` | ROA, morosidad, solvencia, tasas activa/pasiva |
| `indicadores/morosidad-estresada` | Morosidad por componente (vencido, cobranza, reestructurado) |
| `solvencia/componentes` | APR, capital primario/secundario, índice de solvencia |
| `captaciones/localidad` | Depósitos por provincia |

Series macroeconómicas del BCRD (generadas con datos calibrados de informes oficiales):

| Serie | Fuente |
|---|---|
| Tasa de Política Monetaria (TPM) | BCRD informes anuales 2015-2025 |
| IPC (inflación mensual e interanual) | BCRD / Banco Mundial |
| Tipo de cambio DOP/USD | BCRD Mercado Cambiario |
| Remesas en USD millones | BCRD Sector Externo |

---

## Pestañas del dashboard (12)

| Pestaña | Contenido |
|---|---|
| **Inicio** | Presentación del proyecto y autor |
| **Conceptos** | Glosario de términos bancarios y financieros |
| **Captaciones** | Evolución por moneda, top 10 entidades, distribución por tipo de depositante |
| **Cartera de Créditos** | Calidad/morosidad, treemap sectorial, brecha de género |
| **Indicadores** | Apalancamiento, margen, spread de tasas, activos improductivos, ROA, ROE, solvencia |
| **Solvencia** | Evolución de APR y patrimonio técnico + distribución de índices (boxplots) |
| **Estadísticas** | Correlación cruzada macro-banca, histograma, detección de outliers IQR+Z |
| **Macro vs Banca** | TPM vs IPC, TPM vs morosidad, tipo de cambio, eventos históricos |
| **Ranking Bancario** | Podio top/bottom 3, scorecard interactivo con cuota de mercado |
| **Mapa Provincial** | Choropleth GeoJSON + barras de captaciones por provincia |
| **Remesas e Inclusión** | Serie de remesas, correlación con captaciones, brecha de género |
| **Stress Testing** | Modelo OLS (TPM + IPC + TC → morosidad), sliders de escenario, IC 95% |

---

## Estructura del proyecto

```
sif-bancario/
├── config/
│   └── settings.py          # Variables de entorno, URLs, endpoints
├── data/
│   ├── geojson/             # GeoJSON provincias RD (incluido en repo)
│   └── processed/           # CSVs estáticos pre-generados (incluidos en repo)
├── scripts/
│   └── generar_datos.py     # Regenera los CSVs desde la API v2
├── src/
│   ├── api/
│   │   └── client.py        # SBApiClientV2 — paginación automática x-pagination
│   ├── analysis/
│   │   └── statistics.py    # FinancialAnalyzer — CSV → API → MySQL (en ese orden)
│   ├── dashboard/
│   │   ├── app.py           # Dash app — 12 tabs + callbacks
│   │   └── tabs/            # Un módulo por pestaña
│   ├── db/
│   │   ├── connection.py    # SQLAlchemy engine
│   │   └── models.py        # ORM (tablas bancarias + macro)
│   ├── etl/
│   │   └── pipeline.py      # Pipeline ETL completo (para actualización local)
│   └── macro/
│       └── bcrd_data.py     # Series macroeconómicas BCRD
├── run_dashboard.py         # Punto de entrada
├── runtime.txt              # Python 3.11.0 (para Render.com)
├── render.yaml              # Configuración de deploy en Render.com
├── requirements.txt
├── .env.example             # Plantilla de variables de entorno
└── .gitignore
```

---

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/ErickPerezOrtiz/SIF-Bancario-.git
cd SIF-Bancario-

# 2. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate       # Windows
# source venv/bin/activate    # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env
# Editar .env con tu API key de desarrollador.sb.gob.do

# 5. (Opcional) Regenerar los CSVs de datos con la API en vivo
python scripts/generar_datos.py

# 6. Lanzar dashboard
python run_dashboard.py
# → http://localhost:8050
```

> Los CSVs pre-generados ya están incluidos en el repositorio (`data/processed/`), por lo que el paso 5 es opcional. Ejecutarlo cuando quieras actualizar los datos al período más reciente.

### Variables de entorno requeridas (`.env`)

```
SB_API_KEY=<tu_key_de_desarrollador.sb.gob.do>
SB_BASE_URL=https://apis.sb.gob.do/estadisticas
SB_BASE_URL_V2=https://apis.sb.gob.do/estadisticas/v2

# Opcionales — solo si usas MySQL como backend
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sif_bancario
DB_USER=root
DB_PASSWORD=
```

Obtener API key gratis en [desarrollador.sb.gob.do](https://desarrollador.sb.gob.do).

---

## Deploy en Render.com

El repositorio incluye `render.yaml` y `runtime.txt` listos para usar.

1. Hacer fork del repositorio en GitHub
2. En [render.com](https://render.com) → **New Web Service** → conectar el repositorio
3. Render detecta `render.yaml` automáticamente y usa Python 3.11
4. En **Environment Variables**, agregar `SB_API_KEY` con tu key
5. Deploy → la URL pública queda disponible en ~2 minutos

> **Nota:** El plan gratuito de Render hiberna la instancia tras 15 min de inactividad. La primera carga tras hibernación tarda ~30 segundos (cold start). Los datos se leen desde CSVs estáticos incluidos en el repo, por lo que no se necesita conexión a la API en producción.

---

## API de la Superintendencia de Bancos

- **Endpoint base v2**: `https://apis.sb.gob.do/estadisticas/v2/`
- **Autenticación**: header `Ocp-Apim-Subscription-Key`
- **Paginación**: header `x-pagination` → `{"HasNext": true/false, "TotalPages": N, ...}`
- **Documentación**: [desarrollador.sb.gob.do](https://desarrollador.sb.gob.do)

El cliente (`src/api/client.py`) usa `entidad=TODOS&registros=5000` para minimizar el número de páginas (~12 para indicadores financieros vs. ~393 con el enfoque estándar).

---

## 🤖 Desarrollado con apoyo de IA

Este proyecto fue desarrollado con el apoyo de **Claude AI** (Anthropic) como asistente de programación — arquitectura del proyecto, integración con la API de la Superintendencia de Bancos, desarrollo de visualizaciones y ajustes del dashboard.

Las decisiones de análisis financiero, diseño del producto y dirección del proyecto son del autor.

---

**Autor:** [Erick Pérez](https://github.com/ErickPerezOrtiz) · Analítica y Ciencia de Datos · ITLA, Santo Domingo RD
