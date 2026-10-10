# BIOREFINE AI — Real-Time Process Monitoring Dashboard
# Runs with simulated sensor readings. Later, replace get_sensor_readings()
# with actual ESP32/sensor data and configure validated process limits.

import time
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="BIOREFINE AI | Process Monitor",
    page_icon="🌱",
    layout="wide",
)

# -------------------- CONFIGURABLE THRESHOLDS --------------------
# IMPORTANT:
# These are DEMONSTRATION values only, not validated industrial limits.
# Set ranges appropriate to your actual process with your faculty/bioprocess mentor.
PARAMETERS = {
    "Temperature (°C)": {"min": 25.0, "max": 37.0, "unit": "°C"},
    "pH": {"min": 5.0, "max": 7.0, "unit": ""},
    "Moisture (%)": {"min": 40.0, "max": 70.0, "unit": "%"},
    "Pressure (kPa)": {"min": 90.0, "max": 115.0, "unit": " kPa"},
    "Flow rate (L/min)": {"min": 1.0, "max": 10.0, "unit": " L/min"},
}

# -------------------- PAGE STYLE --------------------
st.title("🌱 BIOREFINE AI")
st.subheader("Intelligent Biorefinery Process Monitoring")
st.caption(
    "HackFest 2026 prototype | Demo mode uses simulated sensor readings. "
    "Thresholds must be validated before any real process use."
)

with st.sidebar:
    st.header("⚙️ Monitoring settings")
    demo_mode = st.toggle("Use simulated sensor readings", value=True)
    refresh_seconds = st.slider("Refresh interval (seconds)", 2, 10, 3)
    st.markdown("---")
    st.markdown("### Configurable limits")
    st.caption("Demo limits only — confirm actual limits with your process mentor.")

    limits = {}
    for name, config in PARAMETERS.items():
        st.markdown(f"**{name}**")
        low = st.number_input(
            f"Minimum — {name}",
            value=float(config["min"]),
            key=f"min_{name}",
        )
        high = st.number_input(
            f"Maximum — {name}",
            value=float(config["max"]),
            key=f"max_{name}",
        )
        limits[name] = {"min": low, "max": high, "unit": config["unit"]}

# -------------------- SIMULATED SENSOR DATA --------------------
def get_sensor_readings():
    """Return simulated readings. Replace this function for real sensor integration."""
    import random

    return {
        "Temperature (°C)": round(random.uniform(28.0, 35.0), 1),
        "pH": round(random.uniform(5.5, 6.8), 2),
        "Moisture (%)": round(random.uniform(45.0, 65.0), 1),
        "Pressure (kPa)": round(random.uniform(95.0, 110.0), 1),
        "Flow rate (L/min)": round(random.uniform(2.0, 8.0), 1),
    }

def classify_parameter(name, value, low, high, unit):
    """Classify a reading against the configured range and return message/action."""
    if value < low:
        status = "LOW"
        message = f"{name} is too low ({value}{unit}); permitted demo range is {low}–{high}{unit}."
        action = f"Check the {name.lower()} reading and process settings."
    elif value > high:
        status = "HIGH"
        message = f"{name} is too high ({value}{unit}); permitted demo range is {low}–{high}{unit}."
        action = f"Review the {name.lower()} and follow the approved operating procedure."
    else:
        status = "NORMAL"
        message = f"{name} is within the configured range ({value}{unit})."
        action = "No threshold-based action required; continue monitoring."
    return status, message, action

# -------------------- SESSION STATE --------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# -------------------- DEMO INPUT CONTROLS --------------------
st.markdown("### 🧪 Sensor input")
st.write(
    "Use automatic simulation, or turn it off to manually enter readings and "
    "test how notifications respond."
)

manual_values = {}
if not demo_mode:
    c1, c2, c3 = st.columns(3)
    manual_values["Temperature (°C)"] = c1.number_input(
        "Temperature (°C)", value=30.0, step=0.5
    )
    manual_values["pH"] = c2.number_input("pH", value=6.5, step=0.1, format="%.2f")
    manual_values["Moisture (%)"] = c3.number_input(
        "Moisture (%)", value=55.0, step=1.0
    )
    c4, c5 = st.columns(2)
    manual_values["Pressure (kPa)"] = c4.number_input(
        "Pressure (kPa)", value=101.0, step=1.0
    )
    manual_values["Flow rate (L/min)"] = c5.number_input(
        "Flow rate (L/min)", value=5.0, step=0.5
    )

if demo_mode:
    readings = get_sensor_readings()
else:
    readings = manual_values

# -------------------- EVALUATE ALL PARAMETERS --------------------
results = {}
for name, value in readings.items():
    config = limits[name]
    # Avoid accidentally accepting a reversed range.
    if config["min"] >= config["max"]:
        st.error(f"Configuration error: minimum for {name} must be less than maximum.")
        st.stop()

    status, message, action = classify_parameter(
        name, float(value), config["min"], config["max"], config["unit"]
    )
    results[name] = {
        "value": float(value),
        "status": status,
        "message": message,
        "action": action,
        "min": config["min"],
        "max": config["max"],
    }

abnormal = {name: item for name, item in results.items() if item["status"] != "NORMAL"}
overall_status = "ALERT" if abnormal else "SYSTEM NORMAL"

# -------------------- TOP-LEVEL STATUS --------------------
st.markdown("---")
top1, top2, top3 = st.columns(3)
top1.metric("Overall process status", overall_status)
top2.metric("Parameters monitored", len(results))
top3.metric("Active alerts", len(abnormal))

if abnormal:
    st.error(f"🚨 {len(abnormal)} parameter(s) need attention.")
    for name, item in abnormal.items():
        if item["status"] == "HIGH":
            st.warning(f"🔺 **HIGH — {name}:** {item['message']}")
        else:
            st.warning(f"🔻 **LOW — {name}:** {item['message']}")
        st.info(f"**Suggested response:** {item['action']}")
else:
    st.success("✅ SYSTEM NORMAL — All monitored parameters are within the configured demo ranges.")

# -------------------- PARAMETER CARDS --------------------
st.markdown("### 📊 Live parameter dashboard")
cols = st.columns(len(results))
for col, (name, item) in zip(cols, results.items()):
    with col:
        st.metric(name, f"{item['value']}{PARAMETERS[name]['unit']}")
        if item["status"] == "NORMAL":
            st.success("NORMAL")
        elif item["status"] == "HIGH":
            st.error("HIGH")
        else:
            st.warning("LOW")
        st.caption(f"Allowed demo range: {item['min']}–{item['max']}")

# -------------------- LOG READINGS AND EVENTS --------------------
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
row = {"Timestamp": timestamp, **readings, "Overall status": overall_status}
st.session_state.history.append(row)
st.session_state.history = st.session_state.history[-300:]

for name, item in abnormal.items():
    st.session_state.alerts.append({
        "Timestamp": timestamp,
        "Parameter": name,
        "Value": item["value"],
        "Status": item["status"],
        "Notification": item["message"],
        "Suggested response": item["action"],
    })
st.session_state.alerts = st.session_state.alerts[-300:]

st.markdown("### 📈 Process trend")
history_df = pd.DataFrame(st.session_state.history)
if not history_df.empty:
    selected_parameter = st.selectbox(
        "Choose parameter to plot",
        list(PARAMETERS.keys()),
        key="trend_parameter",
    )
    chart_df = history_df.set_index("Timestamp")[[selected_parameter]]
    st.line_chart(chart_df, height=250)

st.markdown("### 🔔 Alert and event history")
if st.session_state.alerts:
    st.dataframe(pd.DataFrame(st.session_state.alerts[::-1]), use_container_width=True)
else:
    st.info("No alerts recorded in this session.")

with st.expander("View latest raw readings"):
    st.json(readings)

st.caption(
    "Safety note: this dashboard provides monitoring and advisory messages only. "
    "It does not control equipment. Do not use demo thresholds for real fermentation "
    "or industrial operation without process-specific validation."
)

# Auto-refresh only in simulation mode; manual mode remains stable for testing.
if demo_mode:
    time.sleep(refresh_seconds)
    st.rerun()
