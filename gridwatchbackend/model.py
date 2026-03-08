import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib

# load dataset
data = pd.read_csv("training_data.csv")

X = data.drop("outage", axis=1)
y = data["outage"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_leaf=5,
    class_weight="balanced",  # outages are rare — prevents bias toward "no outage"
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

# evaluate
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred, target_names=["No Outage", "Outage"]))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

# feature importance
importances = pd.Series(model.feature_importances_, index=X.columns)
print("\nTop features:")
print(importances.sort_values(ascending=False).to_string())

# save model and feature columns for consistent inference
joblib.dump({"model": model, "features": list(X.columns)}, "outage_model.pkl")

print("\nModel trained and saved.")
