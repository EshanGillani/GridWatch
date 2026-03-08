from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import pandas as pd
import joblib

app = Flask(__name__)
CORS(app)

# Load trained model
artifact = joblib.load("outage_model.pkl")
model = artifact["model"]
features = artifact["features"]

# Supported Virginia cities
CITIES = {
    "richmond": (37.5538, -77.4603),
    "virginia_beach": (36.8529, -75.9780),
    "norfolk": (36.8508, -76.2859),
    "arlington": (38.8816, -77.0910),
    "alexandria": (38.8048, -77.0469),
    "roanoke": (37.2709, -79.9414),
    "charlottesville": (38.0293, -78.4767),
    "newport_news": (37.0871, -76.4730),
    "hampton": (37.0299, -76.3452),
    "chesapeake": (36.7682, -76.2875)
}

def get_weather(city):
    lat, lon = CITIES[city]

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"wind_gusts_10m,precipitation,snowfall,cloud_cover"
        f"&temperature_unit=fahrenheit"
        f"&forecast_days=1"
    )

    response = requests.get(url)
    data = response.json()
    hourly = data["hourly"]

    weather = {
        "temperature_2m": hourly["temperature_2m"][-1],
        "relative_humidity_2m": hourly["relative_humidity_2m"][-1],
        "wind_speed_10m": hourly["wind_speed_10m"][-1],
        "wind_gusts_10m": hourly["wind_gusts_10m"][-1],
        "precipitation": hourly["precipitation"][-1],
        "snowfall": hourly["snowfall"][-1],
        "cloud_cover": hourly["cloud_cover"][-1],
    }

    return weather


@app.route("/api/prediction")
def prediction():

    city = request.args.get("city", "richmond").lower()

    if city not in CITIES:
        return jsonify({
            "error": "City not supported",
            "supported_cities": list(CITIES.keys())
        }), 400

    weather = get_weather(city)

    df = pd.DataFrame([weather])[features]

    risk = model.predict_proba(df)[0][1]

    return jsonify({
        "city": city,
        "weather": weather,
        "outage_risk": float(risk)
    })


@app.route("/")
def home():
    return jsonify({
        "message": "GridWatch API running",
        "endpoint": "/api/prediction?city=richmond",
        "cities": list(CITIES.keys())
    })


if __name__ == "__main__":
    app.run(debug=True)