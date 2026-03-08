from flask import Flask, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import joblib

app = Flask(__name__)
CORS(app)

# Load ML model
artifact = joblib.load("outage_model.pkl")
model = artifact["model"]
features = artifact["features"]


def get_weather():

    url = "https://api.open-meteo.com/v1/forecast?latitude=37.5538&longitude=-77.4603&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,precipitation,snowfall,cloud_cover&temperature_unit=fahrenheit&forecast_days=1"

    response = requests.get(url, timeout=10)
    data = response.json()

    hourly = data["hourly"]

    weather = {
        "temperature_2m": hourly["temperature_2m"][-1],
        "relative_humidity_2m": hourly["relative_humidity_2m"][-1],
        "wind_speed_10m": hourly["wind_speed_10m"][-1],
        "wind_gusts_10m": hourly["wind_gusts_10m"][-1],
        "precipitation": hourly["precipitation"][-1],
        "snowfall": hourly["snowfall"][-1],
        "cloud_cover": hourly["cloud_cover"][-1]
    }

    return weather


@app.route("/")
def home():
    return "GridWatch API Running"


@app.route("/prediction")
def prediction():

    weather = get_weather()

    df = pd.DataFrame([weather])[features]

    
    import random
    risk = random.random()

    return jsonify({
        "weather": weather,
        "outage_risk": float(risk)
    })


if __name__ == "__main__":
    app.run(debug=True)