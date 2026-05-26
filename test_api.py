import requests, os, sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("SB_API_KEY")
base = "https://apis.sb.gob.do/estadisticas"

headers = {
    "Ocp-Apim-Subscription-Key": key,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://desarrollador.sb.gob.do/",
    "Origin": "https://desarrollador.sb.gob.do",
}

endpoints = [
    "captaciones/moneda",
    "captaciones/localidad",
    "captaciones/sector-depositante",
    "carteras/creditos/tipo",
    "carteras/creditos/moneda",
    "indicadores/principales",
    "indicadores/financieros",
    "solvencia/componentes",
    "estados/resultados/eif",
    "estados/situacion/eif",
]

params = {"periodoInicial": "2024-01", "periodoFinal": "2024-03"}
session = requests.Session()

print(f"\nBase URL: {base}")
print(f"Key:      {key[:8]}...{key[-4:]}\n")
print(f"{'Endpoint':<45} {'Status':>7}  {'Registros':>10}")
print("-" * 68)

for ep in endpoints:
    url = f"{base}/{ep}"
    try:
        r = session.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            try:
                data = r.json()
                n = len(data) if isinstance(data, list) else len(data.get("data", [data]))
                print(f"{ep:<45} {r.status_code:>7}  {n:>10} registros")
                if n > 0:
                    sample = data[0] if isinstance(data, list) else data.get("data", [data])[0]
                    keys = list(sample.keys())[:6]
                    print(f"  campos: {keys}")
            except Exception:
                print(f"{ep:<45} {r.status_code:>7}  (no JSON) {r.text[:60]}")
        else:
            body = r.text[:80].replace("\n", " ")
            print(f"{ep:<45} {r.status_code:>7}  {body}")
    except Exception as e:
        print(f"{ep:<45}   ERROR  {str(e)[:60]}")
