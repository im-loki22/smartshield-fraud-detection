import streamlit as st
import json
import os
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="SmartShield Fraud Dashboard", layout="wide")

st.title("🛡️ SmartShield — Real-Time Fraud Monitor")

# -------- Paths --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "..", "data", "transactions_log.json")

# -------- Load Logs --------
def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
        return pd.DataFrame(data)
    return pd.DataFrame()

df = load_logs()

# -------- Metrics --------
col1, col2, col3 = st.columns(3)

total_txn = len(df)
high_risk = len(df[df["risk_level"].str.contains("HIGH", na=False)])
medium_risk = len(df[df["risk_level"].str.contains("MEDIUM", na=False)])

col1.metric("Total Transactions", total_txn)
col2.metric("High Risk 🚨", high_risk)
col3.metric("Medium Risk ⚠️", medium_risk)

st.divider()

# -------- Chart --------
if not df.empty:
    st.subheader("📊 Risk Distribution")
    chart_data = df["risk_level"].value_counts()
    st.bar_chart(chart_data)

    st.subheader("📋 Transaction Log")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No transactions logged yet.")

st.divider()

# -------- Test Transaction Sender --------
st.subheader("🧪 Send Test Transaction")

with st.form("txn_form"):
    transaction_id = st.text_input("Transaction ID", "TXN_TEST_1")
    customer_id = st.text_input("Customer ID", "CUST_TEST_1")
    amount = st.number_input("Amount", value=1000.0)
    transaction_hour = st.slider("Transaction Hour", 0, 23, 12)
    location_risk = st.selectbox("Location Risk", [0, 1])
    device_trust_score = st.slider("Device Trust Score", 0.0, 1.0, 0.8)
    failed_attempts = st.number_input("Failed Attempts", value=0)
    payment_channel = st.selectbox("Payment Channel", ["UPI", "CARD", "NETBANKING"])

    submitted = st.form_submit_button("🚀 Send Transaction")

    if submitted:
        payload = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "amount": amount,
            "transaction_hour": transaction_hour,
            "location_risk": location_risk,
            "device_trust_score": device_trust_score,
            "failed_attempts": failed_attempts,
            "payment_channel": payment_channel
        }

        try:
            response = requests.post(
                "http://127.0.0.1:8000/predict",
                json=payload,
                timeout=5
            )
            st.success(response.json())
        except Exception as e:
            st.error(f"API Error: {e}")