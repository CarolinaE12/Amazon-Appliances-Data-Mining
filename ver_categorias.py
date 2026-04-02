from datasets import load_dataset
import pandas as pd

archivo = "data/Electronics.jsonl.gz"
try:
    df = pd.read_json(archivo, lines=True, compression='gzip', nrows=5000)
    print("¡Archivo cargado con éxito!")
    print("\n Campos (Columnas) detectados ")
    print(df.columns.tolist())
    
    print("\n Vista de datos ")
    print(df[['rating', 'title', 'text']].head())

except Exception as e:
    print(f" Error: {e}")
    print("El Archivo debe estar en la misma carpeta que el .py")
    # Pagina del dataset:https://amazon-reviews-2023.github.io/