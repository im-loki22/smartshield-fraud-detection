from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import joblib
import numpy as np
import os
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ THEN log file
LOG_FILE = os.path.join(BASE_DIR, "..", "data", "transactions_log.json")
CASE_FILE = os.path.join(BASE_DIR, "..", "data", "fraud_cases.json")
QUERY_FILE = os.path.join(BASE_DIR, "..", "data", "customer_queries.json")

def log_transaction(tx, result):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    record = {
        "transaction_id": tx.transaction_id,
        "customer_id": tx.customer_id,
        "amount": tx.amount,
        "channel": tx.payment_channel,
        "risk_score": result["final_risk_score"],
        "risk_level": result["risk_level"]
    }

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(record)

        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print("Logging error:", e)
       
def send_fraud_alert(tx, result):
    # Demo alert (hackathon ready)
    
    if result["final_risk_score"] >= 75:
        print("🚨 FRAUD ALERT TRIGGERED")
        print(f"Customer: {tx.customer_id}")
        print(f"Transaction: {tx.transaction_id}")
        print(f"Amount: ₹{tx.amount}")
        print("Recommended: BLOCK TRANSACTION")

        # future-ready hooks
        # send_email(tx)
        # send_sms(tx)
def create_case(tx, result):
    if result["final_risk_score"] < 75:
         return

    try:
        os.makedirs(os.path.dirname(CASE_FILE), exist_ok=True)

        case = {
            "case_id": f"CASE_{tx.transaction_id}",
            "customer_id": tx.customer_id,
            "transaction_id": tx.transaction_id,
            "risk_score": result["final_risk_score"],
            "status": "OPEN",
            "created_at": datetime.utcnow().isoformat()
        }

        if os.path.exists(CASE_FILE):
            with open(CASE_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(case)

        with open(CASE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print("Case creation error:", e)
app = FastAPI(
    title="SmartShield Fraud Detection API",
    description="AI-powered real-time fraud prevention for digital payments",
    version="1.0"
)
@app.get("/")
def home():
    return {"message": "SmartShield Fraud API Running 🚀"}
# Load trained model
MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "fraud_model.pkl")
model = joblib.load(MODEL_PATH)
# ----------- Request Schema -----------



class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    transaction_hour: int
    location_risk: int
    device_trust_score: float
    failed_attempts: int
    payment_channel: str
    merchant_id: Optional[str] = "UNKNOWN"
    
class CustomerQuery(BaseModel):
    query_id: str
    customer_id: str
    transaction_id: str
    issue_type: str
    message: str
    priority: Optional[str] = "LOW"
    
# ----------- Rule Engine -----------

def rule_engine(tx):
    risk = 0

    if tx.amount > 50000:
        risk += 30

    if tx.failed_attempts > 3:
        risk += 25

    if tx.location_risk == 1:
        risk += 20

    if tx.device_trust_score < 0.3:
        risk += 25

    return min(risk, 100)

# ----------- Risk Level -----------
# ----------- Velocity Engine -----------

def velocity_risk(customer_id):
    try:
        if not os.path.exists(LOG_FILE):
            return 0

        with open(LOG_FILE, "r") as f:
            data = json.load(f)

        # last 5 transactions of this customer
        recent = [
            tx for tx in data
            if tx["customer_id"] == customer_id
        ][-5:]

        # simple bank-style rule
        if len(recent) >= 3:
            return 20  # add extra risk

        return 0

    except Exception as e:
        print("Velocity check error:", e)
        return 0
    # ----------- Time Burst Engine -----------

def time_burst_risk(customer_id):
    try:
        if not os.path.exists(LOG_FILE):
            return 0

        with open(LOG_FILE, "r") as f:
            data = json.load(f)

        # get last few transactions
        recent = [
            tx for tx in data
            if tx["customer_id"] == customer_id
        ][-5:]

        # 🚨 many transactions recently
        if len(recent) >= 4:
            return 15

        return 0

    except Exception as e:
        print("Time burst error:", e)
        return 0
    # ----------- Geo Anomaly Engine -----------

def geo_anomaly_risk(tx):
    try:
        if tx.location_risk == 1 and tx.device_trust_score < 0.4:
            return 25  # very suspicious combo

        if tx.location_risk == 1:
            return 10

        return 0

    except Exception as e:
        print("Geo anomaly error:", e)
        return 0
    # ----------- Geo Risk Engine -----------

def geo_risk(tx):
    risk = 0

    # already high-risk location
    if tx.location_risk == 1:
        risk += 15

    # night suspicious activity
    if tx.transaction_hour < 5 or tx.transaction_hour > 23:
        risk += 10

    return risk
    
# ----------- Action Engine -----------
def get_action(score):
    if score >= 80:
        return "BLOCK + ALERT + FREEZE 🛑"
    elif score >= 60:
        return "STEP-UP + OTP 🔐"
    elif score >= 40:
        return "MONITOR 👀"
    else:
        return "ALLOW ✅"

# ----------- Main Prediction API -----------

@app.post("/predict")
def predict_fraud(tx: Transaction):
    features = np.array([[
        tx.amount,
        tx.transaction_hour,
        tx.location_risk,
        tx.device_trust_score,
        tx.failed_attempts
    ]])

    ml_prob = model.predict_proba(features)[0][1] * 100

    # 🔹 Rule engines
    rule_score = rule_engine(tx)
    velocity_score = velocity_risk(tx.customer_id)
    burst_score = time_burst_risk(tx.customer_id)
    geo_score = geo_anomaly_risk(tx)

    # 🔹 Combine rule risks
    combined_rule = min(
        rule_score + velocity_score + burst_score + geo_score,
        100
    )

    # 🔹 FINAL FUSION (bank style)
    final_score = (0.6 * ml_prob) + (0.4 * combined_rule)

    # 🔹 Risk level + action
    risk_level = get_risk_level(final_score)
    action = get_action(final_score)


    risk_level = get_risk_level(final_score)

    result_payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "ml_probability": round(ml_prob, 2),
        "rule_score": rule_score,
        "velocity_score": velocity_score,
        "time_burst_score": burst_score,
        "geo_score": geo_score,
        "final_risk_score": round(final_score, 2),
        "risk_level": risk_level,
        "recommended_action": (
            "BLOCK TRANSACTION" if final_score >= 75
            else "STEP-UP AUTHENTICATION" if final_score >= 40
            else "ALLOW"
        )
    }

    log_transaction(tx, result_payload)
    send_fraud_alert(tx, result_payload)
    create_case(tx, result_payload)
    return result_payload


@app.get("/transaction/{transaction_id}")
def get_transaction(transaction_id: str):
    try:
        if not os.path.exists(LOG_FILE):
            return {"status": "No transactions found"}

        with open(LOG_FILE, "r") as f:
            data = json.load(f)

        for tx in reversed(data):
            if tx["transaction_id"] == transaction_id:
                return {
                    "status": "FOUND ✅",
                    "transaction": tx
                }

        return {"status": "NOT FOUND ❌"}

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/customer/query")
def submit_query(q: CustomerQuery):
    try:
        os.makedirs(os.path.dirname(QUERY_FILE), exist_ok=True)
        priority = "LOW"
        if q.issue_type.lower() in ["fraud complaint", "unauthorized"]:
            priority = "HIGH"
        record = {
            "query_id": q.query_id,
            "customer_id": q.customer_id,
            "transaction_id": q.transaction_id,
            "issue_type": q.issue_type,
            "message": q.message,
            "status": "OPEN",
            "timestamp": datetime.utcnow().isoformat()
        }

        if os.path.exists(QUERY_FILE):
            with open(QUERY_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(record)

        with open(QUERY_FILE, "w") as f:
            json.dump(data, f, indent=2)

        return {"status": "Query submitted successfully ✅"}

    except Exception as e:
        return {"error": str(e)}