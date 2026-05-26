"""Verificación rápida de los datos de muestra."""
import sys
sys.path.insert(0, ".")
from src.analysis.statistics import FinancialAnalyzer

az = FinancialAnalyzer()

print("=== KPIs Ejecutivos ===")
kpis = az.resumen_ejecutivo()
for k, v in kpis.items():
    if isinstance(v, float) and v > 1000:
        print(f"  {k:30s}: RD$ {v/1e9:,.2f} billones")
    elif isinstance(v, float):
        print(f"  {k:30s}: {v:.4f}")
    else:
        print(f"  {k:30s}: {v}")

print()
print("=== Evolución captaciones (primeros 6 periodos, DOP) ===")
df = az.evolucion_captaciones_mensual()
print(df[df["moneda"] == "DOP"].head(6).to_string(index=False))

print()
print("=== Top 5 entidades por captaciones ===")
print(az.top_entidades_captaciones(5).to_string(index=False))

print()
print("=== Calidad de cartera (últimos 5 meses) ===")
df2 = az.calidad_cartera()
print(df2.tail(5).to_string(index=False))

print()
print("=== Solvencia promedio del sistema (últimos 6 meses) ===")
df3 = az.solvencia_sistema()
sol = df3[df3["componente"] == "Indice de Solvencia"].tail(6)
if sol.empty:
    sol = df3[df3["componente"].str.contains("Solvencia")].tail(6)
print(sol.to_string(index=False))

print()
print("=== Brecha de género (últimos 3 periodos) ===")
print(az.brecha_genero_credito().tail(6).to_string(index=False))

print()
print("=== Sectores económicos (top 5) ===")
print(az.cartera_por_sector().head(5).to_string(index=False))

print()
print("OK — todos los datos listos para el dashboard.")
