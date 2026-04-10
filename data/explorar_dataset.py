# Este script cuenta el total de registros del dataset.
# Requiere el archivo:
# data/Electronics.jsonl.gz
# (No incluido en el repositorio por su tamaño)
import gzip

with gzip.open("data/Electronics.jsonl.gz", "rt", encoding="utf-8") as f:
    total = sum(1 for _ in f)

print("Total:", total)