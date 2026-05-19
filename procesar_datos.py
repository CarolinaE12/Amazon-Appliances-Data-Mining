import pandas as pd
import json
import os

# scikit-learn para el análisis predictivo
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np

ARCHIVO_ENTRADA = "data/Electronics.jsonl.gz"
ARCHIVO_BA      = "data/business_analytics.json"
ARCHIVO_MINING  = "data/data_mining.json"

N_FILAS    = 200_000
CHUNK_SIZE = 20_000

# ================================================================
# CATEGORÍAS DE CAUSA DE DEVOLUCIÓN
# ================================================================
CAUSAS = {
    "calidad_producto": [
        "broken", "defective", "not working", "stopped working",
        "poor quality", "cheaply made", "fell apart", "broke",
        "cheap", "flimsy", "terrible quality"
    ],
    "estado_entrega": [
        "damaged", "arrived broken", "crushed", "dented",
        "scratched", "box was damaged", "bent",
        "cracked", "shattered", "smashed"
    ],
    "no_es_lo_descrito": [
        "not as described", "misleading", "fake", "counterfeit",
        "not what i expected", "wrong item", "different from",
        "false advertising"
    ],
    "problemas_software": [
        "error", "bug", "crash", "freezes", "not compatible",
        "driver", "firmware", "wont connect",
        "connection issues", "bluetooth", "wifi issue"
    ],
    "olor_sustancias": [
        "smell", "odor", "gasoline", "chemical smell",
        "burning smell", "smoke"
    ],
    "devolucion_explicita": [
        "return", "returning", "returned", "sent back",
        "refund", "exchange", "replacement"
    ]
}

TIPOS_PRODUCTO = {
    "auriculares":  ["headphone", "earphone", "earbud", "headset", "speaker"],
    "camaras":      ["camera", "lens", "gopro", "webcam", "camcorder"],
    "cables":       ["cable", "charger", "cord", "adapter", "usb", "hdmi"],
    "computadoras": ["laptop", "computer", "tablet", "keyboard", "mouse"],
    "telefonia":    ["phone", "iphone", "android", "samsung", "case"],
    "redes":        ["router", "wifi", "network", "modem", "ethernet"],
    "baterias":     ["battery", "power bank", "solar"],
    "smartwatch":   ["watch", "fitbit", "tracker", "band", "garmin"],
}

TODAS_PALABRAS = [p for lista in CAUSAS.values() for p in lista]


def clasificar_causa(texto):
    for causa, palabras in CAUSAS.items():
        if any(p in texto for p in palabras):
            return causa
    return "sin_causa"


def clasificar_tipo(titulo):
    titulo = str(titulo).lower()
    for tipo, palabras in TIPOS_PRODUCTO.items():
        if any(p in titulo for p in palabras):
            return tipo
    return "otro"


def procesar_dataset():
    print("=" * 50)
    print(f"Procesando en chunks de {CHUNK_SIZE} filas")
    print(f"Límite total: {N_FILAS} filas")
    print("=" * 50)

    columnas = ['rating', 'title', 'text', 'asin',
                'timestamp', 'helpful_vote', 'verified_purchase']

    # Acumuladores
    total_filas       = 0
    suma_ratings      = 0.0
    suma_verificados  = 0
    dist_ratings      = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    stats_tiempo      = {}
    causas_conteo     = {}
    fallas_por_tipo   = {}
    fallas_por_mes    = {}
    fallas_por_fecha  = {}
    fallas_por_rating = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_por_rating  = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_fallas      = 0
    alto_impacto      = 0
    bajo_impacto      = 0
    ejemplos_criticos = []
    muestra_predictivo = []

    # Para ver qué títulos caen en "otro" — acumulamos los primeros 2000
    titulos_sin_clasificar = []

    chunks_leidos = 0

    try:
        lector = pd.read_json(
            ARCHIVO_ENTRADA,
            lines=True,
            compression="gzip",
            chunksize=CHUNK_SIZE
        )

        for chunk in lector:
            if N_FILAS is not None and total_filas >= N_FILAS:
                break

            chunks_leidos += 1
            cols_disponibles = [c for c in columnas if c in chunk.columns]
            chunk = chunk[cols_disponibles].copy()
            chunk = chunk.dropna(subset=["rating", "text"]).copy()

            if chunk.empty:
                continue

            if N_FILAS is not None:
                espacio = N_FILAS - total_filas
                if len(chunk) > espacio:
                    chunk = chunk.head(espacio)

            # Transformaciones
            chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], unit='ms', errors='coerce')
            chunk['fecha'] = chunk['timestamp'].dt.strftime('%Y-%m')
            chunk['mes']   = chunk['timestamp'].dt.month

            chunk['texto_minable'] = (
                chunk['title'].fillna('') + " " + chunk['text'].fillna('')
            ).str.lower()

            chunk['es_falla'] = chunk['texto_minable'].apply(
                lambda x: any(p in x for p in TODAS_PALABRAS)
            )

            chunk_fallas = chunk[chunk['es_falla']].copy()
            if not chunk_fallas.empty:
                chunk_fallas['causa']         = chunk_fallas['texto_minable'].apply(clasificar_causa)
                chunk_fallas['tipo_producto'] = chunk_fallas['title'].apply(clasificar_tipo)

                # Guardar títulos que caen en "otro" para analizarlos
                if len(titulos_sin_clasificar) < 2000:
                    otros = chunk_fallas[chunk_fallas['tipo_producto'] == 'otro']['title'].dropna().tolist()
                    titulos_sin_clasificar.extend(otros)

            # Acumular contadores
            n = len(chunk)
            total_filas      += n
            suma_ratings     += chunk['rating'].sum()
            suma_verificados += chunk['verified_purchase'].sum()

            for r, cnt in chunk['rating'].value_counts().items():
                r_int = int(r)
                if r_int in dist_ratings:
                    dist_ratings[r_int]     += int(cnt)
                    total_por_rating[r_int] += int(cnt)

            for fecha, cnt in chunk.groupby('fecha').size().items():
                stats_tiempo[str(fecha)] = stats_tiempo.get(str(fecha), 0) + int(cnt)

            if len(muestra_predictivo) < 20_000:
                cols_pred = ['rating', 'mes', 'es_falla', 'helpful_vote', 'verified_purchase']
                cols_pred = [c for c in cols_pred if c in chunk.columns]
                muestra_predictivo.append(chunk[cols_pred])

            if not chunk_fallas.empty:
                total_fallas += len(chunk_fallas)

                for causa, cnt in chunk_fallas['causa'].value_counts().items():
                    causas_conteo[str(causa)] = causas_conteo.get(str(causa), 0) + int(cnt)

                for tipo, cnt in chunk_fallas['tipo_producto'].value_counts().items():
                    fallas_por_tipo[str(tipo)] = fallas_por_tipo.get(str(tipo), 0) + int(cnt)

                for mes, cnt in chunk_fallas['mes'].value_counts().items():
                    if pd.notna(mes):
                        fallas_por_mes[str(int(mes))] = fallas_por_mes.get(str(int(mes)), 0) + int(cnt)

                for fecha, cnt in chunk_fallas.groupby('fecha').size().items():
                    fallas_por_fecha[str(fecha)] = fallas_por_fecha.get(str(fecha), 0) + int(cnt)

                for r, cnt in chunk_fallas['rating'].value_counts().items():
                    r_int = int(r)
                    if r_int in fallas_por_rating:
                        fallas_por_rating[r_int] += int(cnt)

                if 'helpful_vote' in chunk_fallas.columns:
                    alto_impacto += int((chunk_fallas['helpful_vote'] >= 100).sum())
                    bajo_impacto += int((chunk_fallas['helpful_vote'] <  100).sum())
                    top_chunk = chunk_fallas.sort_values('helpful_vote', ascending=False).head(5)
                    ejemplos_criticos.extend(json.loads(top_chunk.to_json(orient="records")))

            print(f"  Chunk {chunks_leidos:>3} → {total_filas:>7} filas procesadas", end="\r")

        print(f"\n  Total procesado: {total_filas} filas en {chunks_leidos} chunks")

        # ============================================================
        # ANÁLISIS PREDICTIVO
        # ============================================================
        print("  Entrenando modelo predictivo...")

        df_pred = pd.concat(muestra_predictivo, ignore_index=True).head(20_000)
        df_pred = df_pred.dropna(subset=['rating', 'mes', 'es_falla'])

        X = df_pred[['rating', 'mes']].values
        y = df_pred['es_falla'].astype(int).values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        modelo = LogisticRegression(max_iter=200)
        modelo.fit(X_train, y_train)

        y_pred    = modelo.predict(X_test)
        precision = round(accuracy_score(y_test, y_pred) * 100, 1)

        mes_promedio = 7
        probabilidades = {}
        for r in [1, 2, 3, 4, 5]:
            prob = modelo.predict_proba([[r, mes_promedio]])[0][1]
            probabilidades[str(r)] = round(prob * 100, 1)

        fechas_ord = sorted(fallas_por_fecha.items())[-6:]
        if len(fechas_ord) >= 3:
            valores_rec = [v for _, v in fechas_ord]
            cambios     = [valores_rec[i+1] - valores_rec[i] for i in range(len(valores_rec)-1)]
            pendiente   = sum(cambios) / len(cambios)
            ultimo_mes  = fechas_ord[-1][0]
            ultimo_val  = fechas_ord[-1][1]
            anio, mes_n = int(ultimo_mes[:4]), int(ultimo_mes[5:])
            proyeccion  = {}
            val_actual  = ultimo_val
            for _ in range(3):
                mes_n += 1
                if mes_n > 12:
                    mes_n = 1
                    anio += 1
                fecha_nueva = f"{anio}-{mes_n:02d}"
                val_actual  = max(0, val_actual + pendiente)
                proyeccion[fecha_nueva] = round(val_actual)
        else:
            proyeccion = {}

        predictivo = {
            "precision_modelo":         precision,
            "probabilidades_falla":     probabilidades,
            "tendencia_proximos_meses": proyeccion,
            "nota": (
                f"Modelo entrenado con {len(X_train)} reseñas. "
                f"Variables usadas: rating del producto y mes de la reseña."
            )
        }

        print(f"  Precisión del modelo: {precision}%")

        # ============================================================
        # ARMAR JSONs FINALES
        # ============================================================
        stats_tiempo_ordenado     = dict(sorted(stats_tiempo.items())[-12:])
        fallas_por_fecha_ordenado = dict(sorted(fallas_por_fecha.items())[-12:])
        fallas_por_mes_ordenado   = dict(sorted(fallas_por_mes.items(), key=lambda x: int(x[0])))

        tasa_falla_por_rating = {}
        for r in [1, 2, 3, 4, 5]:
            total_r  = total_por_rating.get(r, 0)
            fallas_r = fallas_por_rating.get(r, 0)
            if total_r > 0:
                tasa_falla_por_rating[str(r)] = round(fallas_r / total_r * 100, 1)

        resumen_ba = {
            "kpis": {
                "total_reviews":         total_filas,
                "promedio_rating":        round(suma_ratings / total_filas, 2),
                "porcentaje_verificados": round(suma_verificados / total_filas * 100, 2)
            },
            "graficos": {
                "ratings": {str(k): v for k, v in dist_ratings.items()},
                "tiempo":  stats_tiempo_ordenado
            },
            "exploratorio": {
                "tasa_falla_por_rating": tasa_falla_por_rating,
                "fallas_por_mes":        fallas_por_mes_ordenado,
            },
            "predictivo": predictivo
        }

        resumen_mining = {
            "conteo_fallas":         total_fallas,
            "porcentaje_fallas":     round(total_fallas / total_filas * 100, 2),
            "causas_principales":    causas_conteo,
            "fallas_por_tipo":       fallas_por_tipo,
            "fallas_por_mes":        fallas_por_mes_ordenado,
            "fallas_por_fecha":      fallas_por_fecha_ordenado,
            "fallas_por_rating":     {str(k): v for k, v in fallas_por_rating.items()},
            "tasa_falla_por_rating": tasa_falla_por_rating,
            "impacto": {
                "alto_impacto": alto_impacto,
                "bajo_impacto": bajo_impacto
            },
            "ejemplos_criticos": ejemplos_criticos[:10]
        }

        if not os.path.exists('data'):
            os.makedirs('data')

        with open(ARCHIVO_BA, 'w', encoding='utf-8') as f:
            json.dump(resumen_ba, f, indent=4, ensure_ascii=False)

        with open(ARCHIVO_MINING, 'w', encoding='utf-8') as f:
            json.dump(resumen_mining, f, indent=4, ensure_ascii=False)

        # ============================================================
        # REPORTE FINAL EN TERMINAL
        # ============================================================
        print("\n¡ÉXITO! Archivos generados en /data")
        print(f"  Fallas:           {total_fallas} ({round(total_fallas/total_filas*100,2)}%)")
        print(f"  Causa principal:  {max(causas_conteo, key=causas_conteo.get)}")
        print(f"  Tipo más común:   {max(fallas_por_tipo, key=fallas_por_tipo.get)}")
        print(f"  Precisión modelo: {precision}%")

        # Mostrar qué títulos caen en "otro" para mejorar el diccionario
        print("\n--- Top 20 títulos sin clasificar (caen en 'otro') ---")
        print(f"  Total 'otro': {fallas_por_tipo.get('otro', 0)} fallas")
        if titulos_sin_clasificar:
            conteo_otros = pd.Series(titulos_sin_clasificar).value_counts().head(20)
            print(conteo_otros.to_string())
        print("------------------------------------------------------")
        print("  → Agrega palabras clave de estos títulos a TIPOS_PRODUCTO")

    except FileNotFoundError:
        print(f"\nERROR: No se encontró {ARCHIVO_ENTRADA}")
    except Exception as e:
        print(f"\nERROR: {e}")
        raise


if __name__ == "__main__":
    procesar_dataset()