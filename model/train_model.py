import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

np.random.seed(42)
n = 5000

data = pd.DataFrame({
    "amount": np.random.exponential(scale=2000, size=n),
    "hour": np.random.randint(0, 24, size=n),
    "distance_from_last_txn": np.random.exponential(scale=50, size=n),
    "velocity_1h": np.random.randint(1, 10, size=n),
    "is_foreign_device": np.random.randint(0, 2, size=n),
})

data["is_fraud"] = (
    (data["amount"] > 5000).astype(int) |
    (data["distance_from_last_txn"] > 100).astype(int) |
    (data["velocity_1h"] > 5).astype(int)
)

X = data.drop("is_fraud", axis=1)
y = data["is_fraud"]

model = RandomForestClassifier(n_estimators=120, random_state=42)
model.fit(X, y)

os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/fraud_model.pkl")

print("✅ Model trained and saved!")