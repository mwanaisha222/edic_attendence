# app.py
import streamlit as st
from datetime import datetime
import pandas as pd
import json
import os
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
NFC_MAPPING_FILE = "nfc_mapping.json"

# ---------- HELPER FUNCTIONS ----------
def load_nfc_mapping():
    """Load NFC tag to username mapping"""
    if os.path.exists(NFC_MAPPING_FILE):
        with open(NFC_MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_nfc_mapping(mapping):
    """Save NFC tag to username mapping"""
    with open(NFC_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)

def perform_check_in(name, discipline, status_choice):
    """Record attendance check-in"""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
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
    
    return status, current_time

# ---------- NFC FUNCTIONS ----------
def nfc_reader_component():
    """HTML component for NFC reading"""
    return f"""
    <script>
    async function readNFC() {{
        if (!("NDEFReader" in window)) {{
            alert("Web NFC is not supported in this browser. Please use Chrome on Android.");
            return;
        }}
        
        try {{
            const ndef = new NDEFReader();
            await ndef.scan();
            
            ndef.onreading = event => {{
                const decoder = new TextDecoder();
                for (const record of event.message.records) {{
                    if (record.recordType === "text") {{
                        const text = decoder.decode(record.data);
                        // Send tag data to Streamlit
                        window.parent.postMessage({{
                            type: 'nfcTagRead',
                            data: text
                        }}, '*');
                    }}
                }}
            }};
            
            document.getElementById("nfcStatus").innerText = "Ready - Tap NFC tag";
        }} catch (error) {{
            document.getElementById("nfcStatus").innerText = `Error: ${{error.message}}`;
        }}
    }}
    </script>
    
    <button onclick="readNFC()" style="
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 10px;
    ">Scan NFC Tag</button>
    <div id="nfcStatus" style="margin-top: 10px; color: #555;">Click to start NFC scanning</div>
    """

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Intern Attendance System", page_icon="📋")

# Initialize session state
if 'nfc_tag' not in st.session_state:
    st.session_state.nfc_tag = None
if 'nfc_username' not in st.session_state:
    st.session_state.nfc_username = None

# ---------- LOGIN ----------
st.sidebar.header("🔐 Login")
login_method = st.sidebar.radio("Login Method", ["Manual", "NFC"])

if login_method == "Manual":
    username = st.sidebar.text_input("Username")
    pin = st.sidebar.text_input("PIN", type="password")
    
    if username and pin:
        if username not in USER_DB or USER_DB[username] != pin:
            st.sidebar.error("Invalid credentials")
            st.stop()
        else:
            st.sidebar.success("Logged in!")
            name = username.capitalize()
            st.session_state.logged_in = True
            st.session_state.current_user = name
else:  # NFC Login
    st.sidebar.info("Use NFC tag to login")
    
    # Load NFC mapping
    nfc_mapping = load_nfc_mapping()
    
    # Display NFC reader component
    components.html(nfc_reader_component(), height=150)
    
    # Handle NFC tag reads
    nfc_data = st.empty()
    if st.session_state.nfc_tag:
        nfc_data.info(f"Scanned NFC Tag: {st.session_state.nfc_tag}")
        
        # Lookup username from NFC tag
        username = nfc_mapping.get(st.session_state.nfc_tag)
        
        if username and username in USER_DB:
            st.sidebar.success(f"Welcome {username.capitalize()}!")
            name = username.capitalize()
            st.session_state.logged_in = True
            st.session_state.current_user = name
            st.session_state.nfc_username = username
        else:
            st.sidebar.error("Unregistered NFC tag")
    
    # Manual fallback
    if st.sidebar.button("Manual Login Fallback"):
        st.session_state.logged_in = False
        st.session_state.nfc_tag = None

# If not logged in, stop execution
if not st.session_state.get('logged_in', False):
    st.stop()

# ---------- MAIN PAGE ----------
name = st.session_state.current_user
st.title(f"📋 Intern Attendance System - Welcome {name}!")

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
if st.button("✅ Check In") or st.session_state.nfc_username:
    # For NFC users, auto check-in when tag is scanned
    if st.session_state.nfc_username:
        username = st.session_state.nfc_username
        name = username.capitalize()
    
    status, current_time = perform_check_in(name, discipline, status_choice)
    st.success(f"Attendance recorded as **{status}** at {current_time}")
    
    # Reset NFC state after check-in
    st.session_state.nfc_tag = None
    st.session_state.nfc_username = None

# ---------- ADMIN VIEW ----------
with st.expander("🔐 Admin Panel"):
    admin_tab, nfc_tab = st.tabs(["Attendance Logs", "NFC Management"])
    
    with admin_tab:
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
    
    with nfc_tab:
        st.subheader("📱 NFC Tag Management")
        nfc_mapping = load_nfc_mapping()
        
        # Display current mappings
        if nfc_mapping:
            st.write("Current NFC Tag Assignments:")
            for tag, user in nfc_mapping.items():
                st.write(f"- `{tag}` → **{user}**")
        else:
            st.info("No NFC tags registered yet")
        
        # Registration form
        st.subheader("Register New NFC Tag")
        new_username = st.selectbox("Select user", list(USER_DB.keys()))
        
        # NFC scanning for registration
        st.markdown("### Scan NFC Tag for Registration")
        components.html(nfc_reader_component(), height=150)
        
        if st.session_state.nfc_tag:
            st.info(f"Scanned Tag: `{st.session_state.nfc_tag}`")
            
            if st.button(f"Assign to {new_username}"):
                # Update mapping
                nfc_mapping[st.session_state.nfc_tag] = new_username
                save_nfc_mapping(nfc_mapping)
                st.success(f"Tag assigned to {new_username}!")
                st.session_state.nfc_tag = None

# Listen for NFC events from JavaScript
components.html("""
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === 'nfcTagRead') {
        Streamlit.setComponentValue(event.data.data);
    }
});
</script>
""", height=0)

# Handle NFC tag data from JavaScript
nfc_tag_data = components.html("", key="nfc_listener")
if nfc_tag_data:
    st.session_state.nfc_tag = nfc_tag_data
    st.experimental_rerun()