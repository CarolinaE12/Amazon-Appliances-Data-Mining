import pandas as pd
import json
import os

# Configuración de rutas
ARCHIVO_ENTRADA = "data/Electronics.jsonl.gz"
ARCHIVO_BA = "data/business_analytics.json"
ARCHIVO_MINING = "data/data_mining.json"

def procesar_dataset(n_filas=50000):
    print(f"--- Iniciando procesamiento de {n_filas} filas ---")
    try:
        # 1. Carga de datos
        columnas = ['rating', 'title', 'text', 'asin', 'timestamp', 'helpful_vote', 'verified_purchase']
        df = pd.read_json(ARCHIVO_ENTRADA, lines=True, compression="gzip", nrows=n_filas)[columnas].copy()

        # 2. Limpieza inicial (creamos una copia para trabajar seguros)
        df = df.dropna(subset=["rating", "text"]).copy()
        
        # 3. Transformaciones usando .loc (EVITA WARNINGS AMARILLOS)
        # Convertimos timestamp a fecha legible
        df.loc[:, 'timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
        df.loc[:, 'fecha'] = df['timestamp'].dt.strftime('%Y-%m')
        
        # Unimos título y texto para minería
        df.loc[:, 'texto_minable'] = (df['title'].fillna('') + " " + df['text'].fillna('')).str.lower()
        
        # Detección de fallas
        palabras_falla = ["broken", "defective", "not working", "damaged", "return", "gasoline", "smell", "roto", "malo", "error"]
        df.loc[:, 'es_falla'] = df['texto_minable'].apply(lambda x: any(p in x for p in palabras_falla))

        # --- PREPARACIÓN JSON: BUSINESS ANALYTICS ---
        # Convertimos llaves y valores a tipos nativos de Python para evitar errores de serialización
        dist_ratings = {str(int(k)): int(v) for k, v in df['rating'].value_counts().sort_index().to_dict().items()}
        stats_tiempo = {str(k): int(v) for k, v in df.groupby('fecha').size().tail(12).to_dict().items()}

        resumen_ba = {
            "kpis": {
                "total_reviews": int(len(df)),
                "promedio_rating": round(float(df['rating'].mean()), 2),
                "porcentaje_verificados": round(float(df['verified_purchase'].mean() * 100), 2)
            },
            "graficos": {
                "ratings": dist_ratings,
                "tiempo": stats_tiempo
            }
        }

        # --- PREPARACIÓN JSON: DATA MINING ---
        # Extraemos palabras más comunes en las fallas
        top_words = df[df['es_falla']]['texto_minable'].str.split().explode().value_counts().head(15).to_dict()
        
        resumen_mining = {
            "conteo_fallas": int(df['es_falla'].sum()),
            "porcentaje_fallas": round(float(df['es_falla'].mean() * 100), 2),
            "palabras_clave": {str(k): int(v) for k, v in top_words.items()},
            # Convertimos ejemplos a formato JSON compatible usando el truco de doble conversión
            "ejemplos_criticos": json.loads(df[df['es_falla']].sort_values(by='helpful_vote', ascending=False).head(10).to_json(orient="records"))
        }

        # 4. Guardado de archivos
        if not os.path.exists('data'): os.makedirs('data')

        with open(ARCHIVO_BA, 'w', encoding='utf-8') as f:
            json.dump(resumen_ba, f, indent=4, ensure_ascii=False)

        with open(ARCHIVO_MINING, 'w', encoding='utf-8') as f:
            json.dump(resumen_mining, f, indent=4, ensure_ascii=False)

        print(f"--- ¡ÉXITO! Archivos generados correctamente en /data ---")

    except Exception as e:
        print(f"Error crítico en el proceso: {e}")

if __name__ == "__main__":
    procesar_dataset(50000)