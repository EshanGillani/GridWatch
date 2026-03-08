import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

# Example training data (simple demo data)
data = {
    "temperature_2m": [30, 40, 50, 60, 70, 80],
    "relative_humidity_2m": [80, 70, 60, 50, 40, 30],
    "wind_speed_10m": [5, 10, 15, 20, 25, 30],
    "wind_gusts_10m": [10, 20, 30, 40, 50, 60],
    "precipitation": [0, 0.1, 0.2, 0.3, 0.5, 0],
    "snowfall": [0, 0, 0, 0, 0, 0],
    "cloud_cover": [10, 20, 40, 60, 80, 90],
    "outage": [0, 0, 0, 1, 1, 1]
}

df = pd.DataFrame(data)

X = df.drop("outage", axis=1)
y = df["outage"]

model = RandomForestClassifier()
model.fit(X, y)

artifact = {
    "model": model,
    "features": X.columns.tolist()
}

joblib.dump(artifact, "outage_model.pkl")

print("Model trained and saved.")