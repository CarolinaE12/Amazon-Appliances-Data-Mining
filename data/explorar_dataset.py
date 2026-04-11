# Este script cuenta el total de registros del dataset.
# Requiere el archivo:
# data/Electronics.jsonl.gz
# (No incluido en el repositorio por su tamaño)

# Importación de librerías
import gzip   # Manejo de archivos comprimidos (.gz)
import json   # Lectura y escritura de datos en formato JSON

# Ruta del archivo del dataset
archivo = "data/Electronics.jsonl.gz"

# Variables de control
contador = 0     # Contador de registros
muestra = []     # Lista para almacenar una muestra

# Lectura del archivo comprimido
with gzip.open(archivo, "rt", encoding="utf-8") as f:
    for linea in f:  # Cada línea corresponde a un registro JSON
        contador += 1

        # Almacenar solo los primeros 5 registros
        if len(muestra) < 5:
            dato = json.loads(linea)  # Conversión de texto JSON a diccionario
            muestra.append(dato)

# Salida del total de registros
print("Total de registros:", contador)

# Salida de una muestra de datos
print("\nMuestra de datos:")

for i, dato in enumerate(muestra, 1):
    print(f"\nRegistro {i}:")
    print("Rating:", dato.get("rating"))
    print("Título:", dato.get("title"))
    # Mostrar solo los primeros 100 caracteres del texto
    print("Texto:", dato.get("text")[:100], "...")