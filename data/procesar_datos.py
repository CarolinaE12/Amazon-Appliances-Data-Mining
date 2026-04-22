import pandas as pd

print("Procesando datos...")

archivo = "data/Electronics.jsonl.gz"

# 1) Cargar muestra
df = pd.read_json(
    archivo,
    lines=True,
    compression="gzip",
    nrows=10000
)

# 2) Columnas útiles
df = df[["rating", "text", "title"]]

# 3) Limpieza
df = df.dropna(subset=["rating", "text"])
df = df.drop_duplicates(subset=["rating", "text"])

df.loc[:, "text"] = df["text"].str.lower().str.strip()

df = df[df["text"] != ""]
df = df[df["rating"].between(1, 5)]

# 4) Detección de fallas
palabras_falla = ["broken", "defective", "not working", "damaged"]

df.loc[:, "falla"] = df["text"].apply(
    lambda x: any(p in x for p in palabras_falla)
)

# 5) MÉTRICAS

# Histograma ratings
rating_counts = df["rating"].value_counts().sort_index().to_dict()

# Pastel fallas (IMPORTANTE: formato JS compatible)
fallas_counts = {
    "true": int(df["falla"].sum()),
    "false": int((~df["falla"]).sum())
}

# Resumen
resumen = {
    "total_reviews": int(len(df)),
    "promedio_rating": float(df["rating"].mean()),
    "porcentaje_fallas": float(df["falla"].mean() * 100),
    "ratings": rating_counts,
    "fallas": fallas_counts
}

# 6) Guardar JSON
pd.DataFrame([resumen]).to_json("data/resumen.json", orient="records")

# 7) Muestra
df[["rating", "title", "text"]].head(10).to_json(
    "data/muestra.json",
    orient="records"
)

print("Datos procesados correctamente")