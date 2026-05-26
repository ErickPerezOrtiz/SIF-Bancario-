# SIF — Banca Dominicana

**Sistema de Inteligencia Financiera · Portafolio · Erick Pérez · ITLA, Santo Domingo RD**

Dashboard interactivo de análisis del sistema bancario dominicano, con datos reales de la API pública de la **Superintendencia de Bancos de la República Dominicana** (2015-2025).

🔗 **Demo:** [sif-bancario.onrender.com](https://sif-bancario.onrender.com)

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Dashboard | Plotly Dash 2.17 + Dash Bootstrap Components 1.6 |
| Análisis | pandas 2.2, numpy 1.26, scipy 1.13, statsmodels 0.14 |
| API | Superintendencia de Bancos RD (Azure APIM) |
| Base de datos | MySQL 8 via SQLAlchemy 2.0 (opcional, fallback a CSV) |
| Mapas | GeoJSON provincias RD + Plotly Choropleth |

---

## Fuente de datos

Los datos provienen directamente de la **API v2 pública** de la Superintendencia de Bancos RD:

| Endpoint | Descripción |
|---|---|
| `indicadores/financieros` | ROE, apalancamiento, margen de intermediación, activos improductivos |
| `indicadores/principales` | ROA, morosidad, solvencia, tasas activa/pasiva |
| `indicadores/morosidad-estresada` | Morosidad por componente (vencido, cobranza, reestructurado) |
| `solvencia/componentes` | APR, capital primario/secundario, índice de solvencia |
| `captaciones/localidad` | Depósitos por provincia |

Series macroeconómicas del BCRD (CSV locales):

| Serie | Fuente |
|---|---|
| Tasa de Política Monetaria (TPM) | BCRD informes anuales |
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
│   └── processed/           # CSVs de fallback y caché GeoJSON (gitignored)
├── src/
│   ├── api/
│   │   └── client.py        # SBApiClientV2 — paginación automática x-pagination
│   ├── analysis/
│   │   └── statistics.py    # FinancialAnalyzer — API v2 → MySQL → CSV
│   ├── dashboard/
│   │   ├── app.py           # Dash app — 12 tabs + callbacks
│   │   └── tabs/            # Un módulo por pestaña
│   ├── db/
│   │   ├── connection.py    # SQLAlchemy engine
│   │   └── models.py        # ORM (tablas bancarias + macro)
│   ├── etl/
│   │   └── pipeline.py      # Pipeline ETL desde la API
│   └── macro/
│       └── bcrd_data.py     # Series macroeconómicas BCRD
├── run_dashboard.py         # Punto de entrada
├── render.yaml              # Configuración de deploy en Render.com
├── requirements.txt
├── .env.example             # Plantilla de variables de entorno
└── .gitignore
```

---

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/ErickPerezOrtiz/sif-bancario.git
cd sif-bancario

# 2. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate       # Windows
# source venv/bin/activate    # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env
# Editar .env con tu API key de desarrollador.sb.gob.do

# 5. Generar datos macro BCRD (para los tabs de Macro y Remesas)
python -c "from src.macro.bcrd_data import generar_macro_completo, guardar_macro_csv; guardar_macro_csv(generar_macro_completo())"

# 6. Lanzar dashboard
python run_dashboard.py
# → http://localhost:8050
```

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

El repositorio incluye `render.yaml` listo para usar.

1. Hacer fork/push a GitHub
2. En [render.com](https://render.com) → **New Web Service** → conectar el repositorio
3. Render detecta `render.yaml` automáticamente
4. En **Environment Variables**, agregar `SB_API_KEY` con tu key
5. Deploy → la URL pública queda disponible en ~2 minutos

> **Nota:** El plan gratuito de Render hiberna la instancia tras 15 min de inactividad. La primera carga después de hibernación tarda ~30 segundos; las subsiguientes son instantáneas. Los datos de indicadores se cachean en memoria tras la primera visita a cada pestaña.

---

## API de la Superintendencia de Bancos

- **Endpoint base v2**: `https://apis.sb.gob.do/estadisticas/v2/`
- **Autenticación**: header `Ocp-Apim-Subscription-Key`
- **Paginación**: header `x-pagination` → `{"HasNext": true/false, "TotalPages": N, ...}`
- **Documentación**: [desarrollador.sb.gob.do](https://desarrollador.sb.gob.do)

El cliente (`src/api/client.py`) usa `entidad=TODOS&registros=5000` para minimizar el número de páginas (~12 para indicadores financieros vs. ~393 con el enfoque estándar).

---

**Autor:** [Erick Pérez](https://github.com/ErickPerezOrtiz) · Analítica y Ciencia de Datos · ITLA, Santo Domingo RD
