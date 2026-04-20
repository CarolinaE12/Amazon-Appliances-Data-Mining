import pandas as pd

print("Ok")

archivo = "data/Electronics.jsonl.gz"

# 1) Cargar muestra segura
df = pd.read_json(
    archivo,
    lines=True,
    compression="gzip",
    nrows=10000
)

# 2) Seleccionar columnas útiles
df = df[["rating", "text", "title"]]

# 3) LIMPIEZA
df = df.dropna(subset=["rating", "text"])
df = df.drop_duplicates(subset=["rating", "text"])

#  evitar warning futuro
df.loc[:, "text"] = df["text"].str.lower().str.strip()

df = df[df["text"] != ""]
df = df[df["rating"].between(1, 5)]

# 4) DETECCIÓN DE FALLAS
palabras_falla = ["broken", "defective", "not working", "damaged"]

df.loc[:, "falla"] = df["text"].apply(
    lambda x: any(p in x for p in palabras_falla)
)

# 5) MÉTRICAS

# Distribución de ratings (histograma)
rating_counts = df["rating"].value_counts().sort_index().to_dict()

# Fallas vs no fallas (pastel)
fallas_counts = df["falla"].value_counts().to_dict()

# Resumen general
resumen = {
    "total_reviews": int(len(df)),
    "promedio_rating": float(df["rating"].mean()),
    "porcentaje_fallas": float(df["falla"].mean() * 100),

    # para gráficas
    "ratings": rating_counts,
    "fallas": fallas_counts
}

# 6) GUARDAR RESULTADO
pd.DataFrame([resumen]).to_json("data/resumen.json", orient="records")

# 7) MUESTRA PARA TABLA
df[["rating", "title", "text"]].head(10).to_json(
    "data/muestra.json",
    orient="records"
)

print(" Datos procesados correctamente")