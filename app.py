from flask import Flask, render_template
import json
import os

app = Flask(__name__)

def cargar_json(nombre):
    ruta = os.path.join("data", nombre)
    if os.path.exists(ruta):
        # El cambio clave es añadir: encoding='utf-8'
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.route("/")
def index():
    return render_template("index.html", ba=cargar_json("business_analytics.json"), 
                           mining=cargar_json("data_mining.json"), active_page='inicio')

@app.route("/analisis")
def analisis():
    return render_template("index.html", ba=cargar_json("business_analytics.json"), 
                           mining=cargar_json("data_mining.json"), active_page='analisis')

@app.route("/reportes")
def reportes():
    return render_template("index.html", ba=cargar_json("business_analytics.json"), 
                           mining=cargar_json("data_mining.json"), active_page='reportes')

if __name__ == "__main__":
    app.run(debug=True)