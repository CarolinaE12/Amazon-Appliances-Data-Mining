from flask import Flask, render_template
import json
import os

# Creamos la aplicación Flask
app = Flask(__name__)

# -------------------------------------------------
# Función auxiliar: carga un archivo JSON de /data/
# -------------------------------------------------
def cargar_json(nombre_archivo):
    ruta = os.path.join("data", nombre_archivo)
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}  # Si no existe el archivo, devuelve vacío

# -------------------------------------------------
# Ruta 1: Página de Inicio  →  /
# -------------------------------------------------
@app.route("/")
def inicio():
    ba     = cargar_json("business_analytics.json")
    mining = cargar_json("data_mining.json")
    # render_template busca el archivo en la carpeta /templates/
    return render_template("index.html", ba=ba, mining=mining)

# -------------------------------------------------
# Ruta 2: Business Analytics  →  /analisis
# -------------------------------------------------
@app.route("/analisis")
def analisis():
    ba = cargar_json("business_analytics.json")
    return render_template("analisis.html", ba=ba)

# -------------------------------------------------
# Ruta 3: Minería de Datos  →  /reportes
# -------------------------------------------------
@app.route("/reportes")
def reportes():
    mining = cargar_json("data_mining.json")
    return render_template("reportes.html", mining=mining)

# -------------------------------------------------
# Arrancar el servidor
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)