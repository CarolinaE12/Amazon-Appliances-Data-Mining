import pandas as pd

archivo = "data/Electronics.jsonl.gz"

# Leer solo 1 fila para inspeccionar nombres de columnas
df_inspector = pd.read_json(archivo, lines=True, compression="gzip", nrows=1)

print("--- Columnas disponibles ---")
print(df_inspector.columns.tolist())
print("\n--- Ejemplo de datos ---")
print(df_inspector.iloc[0])