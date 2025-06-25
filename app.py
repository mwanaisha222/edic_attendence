# app.py

import streamlit as st
from datetime import datetime
import pandas as pd
from urllib.parse import urlparse

# ---------- CONFIG ----------

# Simulated users (username: pin)
USER_DB = {
    "haula": "1234",
    "shakiran": "5678",
    "naomie": "9999"
}

# CSV file to keep backup locally
ATTENDANCE_FILE = "attendance.csv"

# ---------- LOGIN ----------
st.sidebar.header("🔐 Login")
username = st.sidebar.text_input("Username")
pin = st.sidebar.text_input("PIN", type="password")

if username not in USER_DB or USER_DB[username] != pin:
    st.sidebar.error("Invalid credentials")
    st.stop()
else:
    st.sidebar.success("Logged in!")
    name = username.capitalize()

# ---------- PAGE ----------
st.title("📋 Intern Attendance System")

# ---------- GET DISCIPLINE FROM URL ----------
query_params = st.experimental_get_query_params()
discipline = query_params.get("block", [""])[0].capitalize()

if discipline not in ["Civil", "Electrical", "Mechanical"]:
    discipline = st.selectbox("Select your discipline/block", ["Civil", "Electrical", "Mechanical"])
else:
    st.success(f"🧭 Auto-detected block: **{discipline}**")

# ---------- SPECIAL STATUS ----------
status_choice = st.selectbox("Special Status (optional)", ["None", "On Leave", "On Official Duty"])

# ---------- CHECK-IN ----------
if st.button("✅ Check In"):

    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")  # Include full date
    current_hour_min = now.time()

    # Attendance logic
    if status_choice == "On Leave":
        status = "Leave"
    elif status_choice == "On Official Duty":
        status = "Official Duty"
    else:
        if current_hour_min < datetime.strptime("08:00", "%H:%M").time():
            status = "Early"
        elif datetime.strptime("08:00", "%H:%M").time() <= current_hour_min <= datetime.strptime("08:20", "%H:%M").time():
            status = "Late"
        else:
            status = "Absent"

    # Record data
    new_row = {
        "Name": name,
        "Discipline": discipline,
        "Status": status,
        "Time": current_time,
        "Remarks": status_choice if status_choice != "None" else ""
    }

    # Save to local CSV
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "Discipline", "Status", "Time", "Remarks"])

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(ATTENDANCE_FILE, index=False)

    st.success(f"Attendance recorded as **{status}** at {current_time}")

# ---------- ADMIN VIEW ----------
with st.expander("🔐 Admin Panel: View Attendance Logs"):
    try:
        df = pd.read_csv(ATTENDANCE_FILE)

        st.write("📅 Filter attendance records:")
        date_filter = st.text_input("Enter date (YYYY-MM-DD)", value=str(datetime.now().date()))
        discipline_filter = st.selectbox("Select discipline to filter", ["All", "Civil", "Electrical", "Mechanical"])

        # Filter by date
        filtered_df = df[df["Time"].str.startswith(date_filter)]

        # Filter by discipline
        if discipline_filter != "All":
            filtered_df = filtered_df[filtered_df["Discipline"] == discipline_filter]

        st.dataframe(filtered_df)

    except FileNotFoundError:
        st.warning("No attendance records found yet.")
