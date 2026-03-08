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

LAT = 37.5538
LON = -77.4603

def get_weather():

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"wind_gusts_10m,precipitation,snowfall,cloud_cover"
        f"&temperature_unit=fahrenheit"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        current = data["current"]

        weather = {
            "temperature_2m":      current["temperature_2m"],
            "relative_humidity_2m": current["relative_humidity_2m"],
            "wind_speed_10m":      current["wind_speed_10m"],
            "wind_gusts_10m":      current["wind_gusts_10m"],
            "precipitation":       current["precipitation"],
            "snowfall":            current["snowfall"],
            "cloud_cover":         current["cloud_cover"],
        }

        return weather

    except Exception as e:
        print("Weather API error:", e)
        return None


def predict_outage(weather):

    df = pd.DataFrame([weather])

    # Ensure correct feature order
    df = df[features]

    prediction = model.predict_proba(df)[0][1]

    return float(prediction)


@app.route("/")
def home():
    return "GridWatch API Running"


@app.route("/prediction")
def prediction():

    weather = get_weather()

    if weather is None:
        return jsonify({"error": "Weather API failed"}), 500

    outage_risk = predict_outage(weather)

    return jsonify({
        "location": {
            "latitude": LAT,
            "longitude": LON
        },
        "weather": weather,
        "outage_risk": outage_risk
    })


if __name__ == "__main__":
    app.run(debug=True)