import pandas as pd
import json
import os

ARCHIVO_ENTRADA = "data/Electronics.jsonl.gz"
ARCHIVO_BA      = "data/business_analytics.json"
ARCHIVO_MINING  = "data/data_mining.json"

# ================================================================
N_FILAS = 200_000   # procesa 200,000 reseñas
# ================================================================
# TAMAÑO DE CADA CHUNK (pedazo que se lee a la vez)
# ================================================================
CHUNK_SIZE = 20_000    # lee 20,000 a la vez


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

# Lista plana con todas las palabras de falla (para filtro rápido)
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

    # ----------------------------------------------------------------
    # Acumuladores — vamos sumando los resultados de cada chunk
    # ----------------------------------------------------------------
    total_filas         = 0
    suma_ratings        = 0.0
    suma_verificados    = 0
    dist_ratings        = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    stats_tiempo        = {}
    causas_conteo       = {}
    fallas_por_tipo     = {}
    fallas_por_mes      = {}
    fallas_por_fecha    = {}
    fallas_por_rating   = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_por_rating    = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_fallas        = 0
    alto_impacto        = 0
    bajo_impacto        = 0
    ejemplos_criticos   = []   # guardamos los mejores casos

    chunks_leidos = 0

    try:
        # pd.read_json con chunksize lee el archivo de a pedazos
        lector = pd.read_json(
            ARCHIVO_ENTRADA,
            lines=True,
            compression="gzip",
            chunksize=CHUNK_SIZE
        )

        for chunk in lector:

            # ---- Si ya llegamos al límite, paramos ----
            if N_FILAS is not None and total_filas >= N_FILAS:
                break

            chunks_leidos += 1

            # Tomamos solo las columnas que necesitamos
            # (algunas pueden no existir en todos los chunks)
            cols_disponibles = [c for c in columnas if c in chunk.columns]
            chunk = chunk[cols_disponibles].copy()

            # Limpieza básica
            chunk = chunk.dropna(subset=["rating", "text"]).copy()

            # Si el chunk quedó vacío, saltamos
            if chunk.empty:
                continue

            # Si nos pasamos del límite, recortamos el chunk
            if N_FILAS is not None:
                espacio = N_FILAS - total_filas
                if len(chunk) > espacio:
                    chunk = chunk.head(espacio)

            # ---- Transformaciones ----
            chunk['timestamp'] = pd.to_datetime(
                chunk['timestamp'], unit='ms', errors='coerce'
            )
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
                chunk_fallas['causa']        = chunk_fallas['texto_minable'].apply(clasificar_causa)
                chunk_fallas['tipo_producto'] = chunk_fallas['title'].apply(clasificar_tipo)

            # ---- Acumular en los contadores ----
            n = len(chunk)
            total_filas      += n
            suma_ratings     += chunk['rating'].sum()
            suma_verificados += chunk['verified_purchase'].sum()

            # Distribución de ratings
            for r, cnt in chunk['rating'].value_counts().items():
                r_int = int(r)
                if r_int in dist_ratings:
                    dist_ratings[r_int] += int(cnt)
                    total_por_rating[r_int] += int(cnt)

            # Reseñas por mes (YYYY-MM)
            for fecha, cnt in chunk.groupby('fecha').size().items():
                stats_tiempo[str(fecha)] = stats_tiempo.get(str(fecha), 0) + int(cnt)

            if not chunk_fallas.empty:
                total_fallas += len(chunk_fallas)

                # Causas
                for causa, cnt in chunk_fallas['causa'].value_counts().items():
                    causas_conteo[str(causa)] = causas_conteo.get(str(causa), 0) + int(cnt)

                # Tipo de producto
                for tipo, cnt in chunk_fallas['tipo_producto'].value_counts().items():
                    fallas_por_tipo[str(tipo)] = fallas_por_tipo.get(str(tipo), 0) + int(cnt)

                # Mes del año
                for mes, cnt in chunk_fallas['mes'].value_counts().items():
                    if pd.notna(mes):
                        fallas_por_mes[str(int(mes))] = fallas_por_mes.get(str(int(mes)), 0) + int(cnt)

                # Fecha YYYY-MM
                for fecha, cnt in chunk_fallas.groupby('fecha').size().items():
                    fallas_por_fecha[str(fecha)] = fallas_por_fecha.get(str(fecha), 0) + int(cnt)

                # Rating de las fallas
                for r, cnt in chunk_fallas['rating'].value_counts().items():
                    r_int = int(r)
                    if r_int in fallas_por_rating:
                        fallas_por_rating[r_int] += int(cnt)

                # Impacto (votos útiles)
                if 'helpful_vote' in chunk_fallas.columns:
                    alto_impacto += int((chunk_fallas['helpful_vote'] >= 100).sum())
                    bajo_impacto += int((chunk_fallas['helpful_vote'] <  100).sum())

                    # Guardamos los 5 mejores casos de este chunk
                    top_chunk = (
                        chunk_fallas
                        .sort_values('helpful_vote', ascending=False)
                        .head(5)
                    )
                    ejemplos_criticos.extend(
                        json.loads(top_chunk.to_json(orient="records"))
                    )

            print(f"  Chunk {chunks_leidos:>3} → {total_filas:>7} filas procesadas", end="\r")

        print(f"\n  Total procesado: {total_filas} filas en {chunks_leidos} chunks")

        # ----------------------------------------------------------------
        # Ordenar los 10 mejores ejemplos globales
        # ----------------------------------------------------------------
        ejemplos_criticos.sort(key=lambda x: x.get('helpful_vote', 0), reverse=True)
        ejemplos_criticos = ejemplos_criticos[:10]

        # Tomar solo los últimos 12 meses para la gráfica de tiempo
        stats_tiempo_ordenado = dict(
            sorted(stats_tiempo.items())[-12:]
        )
        fallas_por_fecha_ordenado = dict(
            sorted(fallas_por_fecha.items())[-12:]
        )
        fallas_por_mes_ordenado = dict(
            sorted(fallas_por_mes.items(), key=lambda x: int(x[0]))
        )

        # Tasa de falla por rating (%)
        tasa_falla_por_rating = {}
        for r in [1, 2, 3, 4, 5]:
            total_r = total_por_rating.get(r, 0)
            fallas_r = fallas_por_rating.get(r, 0)
            if total_r > 0:
                tasa_falla_por_rating[str(r)] = round(fallas_r / total_r * 100, 1)

        # ----------------------------------------------------------------
        # ARMAR LOS JSONs FINALES
        # ----------------------------------------------------------------
        resumen_ba = {
            "kpis": {
                "total_reviews":         total_filas,
                "promedio_rating":        round(suma_ratings / total_filas, 2),
                "porcentaje_verificados": round(suma_verificados / total_filas * 100, 2)
            },
            "graficos": {
                "ratings": {str(k): v for k, v in dist_ratings.items()},
                "tiempo":  stats_tiempo_ordenado
            }
        }

        resumen_mining = {
            "conteo_fallas":          total_fallas,
            "porcentaje_fallas":      round(total_fallas / total_filas * 100, 2),
            "causas_principales":     causas_conteo,
            "fallas_por_tipo":        fallas_por_tipo,
            "fallas_por_mes":         fallas_por_mes_ordenado,
            "fallas_por_fecha":       fallas_por_fecha_ordenado,
            "fallas_por_rating":      {str(k): v for k, v in fallas_por_rating.items()},
            "tasa_falla_por_rating":  tasa_falla_por_rating,
            "impacto": {
                "alto_impacto": alto_impacto,
                "bajo_impacto": bajo_impacto
            },
            "ejemplos_criticos": ejemplos_criticos
        }

        # ---- Guardar ----
        if not os.path.exists('data'):
            os.makedirs('data')

        with open(ARCHIVO_BA, 'w', encoding='utf-8') as f:
            json.dump(resumen_ba, f, indent=4, ensure_ascii=False)

        with open(ARCHIVO_MINING, 'w', encoding='utf-8') as f:
            json.dump(resumen_mining, f, indent=4, ensure_ascii=False)

        print("\n¡ÉXITO! Archivos generados en /data")
        print(f"  Fallas:          {total_fallas} ({round(total_fallas/total_filas*100,2)}%)")
        print(f"  Causa principal: {max(causas_conteo, key=causas_conteo.get)}")
        print(f"  Tipo más común:  {max(fallas_por_tipo, key=fallas_por_tipo.get)}")

    except FileNotFoundError:
        print(f"\nERROR: No se encontró el archivo {ARCHIVO_ENTRADA}")
        print("Asegúrate de que esté en la carpeta /data/")
    except Exception as e:
        print(f"\nERROR inesperado: {e}")
        raise


if __name__ == "__main__":
    procesar_dataset()