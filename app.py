from flask import Flask, render_template
import pandas as pd
app = Flask(__name__)   

#def cargar_datos():
#   archivo = "data/Electronics.jsonl.gz"
#   df = pd.read_json(archivo, lines=True, compression='gzip', nrows=100)
#    return []

@app.route("/")
def index():
    datos = []
    return render_template("index.html", datos=datos)

if __name__ == "__main__":
    app.run(debug=True)