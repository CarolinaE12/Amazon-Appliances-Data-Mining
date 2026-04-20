from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    with open("data/resumen.json") as f:
        resumen = json.load(f)[0]

    with open("data/muestra.json") as f:
        muestra = json.load(f)

    return render_template("index.html", resumen=resumen, muestra=muestra)

if __name__ == "__main__":
    app.run(debug=True)