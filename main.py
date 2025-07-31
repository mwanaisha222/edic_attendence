import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pandas as pd
import os

# ---------- CONFIG ----------

# Simulated users (username: pin)
USER_DB = {
    "haula": "1234",
    "shakiran": "5678",
    "naomie": "9999"
}

# CSV file to keep backup locally
ATTENDANCE_FILE = "attendance.csv"

# Mapping of NFC/QR tag IDs to disciplines
BLOCK_NFC_QR_MAPPING = {
    "block_civil": "Civil",
    "block_electrical": "Electrical",
    "block_mechanical": "Mechanical"
}

# ---------- HELPER FUNCTIONS ----------
def perform_check_in(name, discipline, status_choice, check_in_time=None):
    """Record attendance check-in"""
    now = check_in_time or datetime.now()
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

# ---------- QR CODE FUNCTIONS ----------
def qr_reader_component():
    """HTML component for QR code scanning"""
    return """
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
    <script>
    let video = null;
    let stream = null;

    async function startQRScanner() {
        try {
            video = document.createElement("video");
            video.setAttribute("playsinline", "true");
            video.style.width = "100%";
            video.style.maxWidth = "300px";
            document.getElementById("qrPreview").appendChild(video);

            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "environment" } 
            });
            video.srcObject = stream;
            await video.play();

            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d");

            function scan() {
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    canvas.height = video.videoHeight;
                    canvas.width = video.videoWidth;
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                    const code = jsQR(imageData.data, imageData.width, imageData.height, {
                        inversionAttempts: "dontInvert"
                    });

                    if (code) {
                        window.parent.postMessage({
                            type: 'qrCodeRead',
                            data: code.data
                        }, '*');
                        stopQRScanner();
                        document.getElementById("qrStatus").innerText = `QR Code Scanned: ${code.data}`;
                    } else {
                        document.getElementById("qrStatus").innerText = "Scanning for QR code...";
                        requestAnimationFrame(scan);
                    }
                } else {
                    requestAnimationFrame(scan);
                }
            }

            document.getElementById("qrStatus").innerText = "Starting QR scanner...";
            requestAnimationFrame(scan);
        } catch (error) {
            document.getElementById("qrStatus").innerText = `Error: ${error.message}`;
        }
    }

    function stopQRScanner() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        if (video) {
            video.remove();
            video = null;
        }
    }
    </script>
    
    <button onclick="startQRScanner()" style="
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 10px;
    ">Scan QR Code</button>
    <div id="qrPreview" style="margin-bottom: 10px;"></div>
    <div id="qrStatus" style="margin-top: 10px; color: #555;">Click to start QR code scanning</div>
    """

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Intern Attendance System", page_icon="📋")

# Initialize session state
if 'nfc_tag' not in st.session_state:
    st.session_state.nfc_tag = None
if 'qr_code' not in st.session_state:
    st.session_state.qr_code = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'discipline' not in st.session_state:
    st.session_state.discipline = None
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

# ---------- LOGIN ----------
st.sidebar.header("🔐 Login")
login_method = st.sidebar.radio("Login Method", ["NFC", "QR Code"])

if login_method == "NFC":
    st.sidebar.info("Scan NFC tag at your discipline block to login")
    
    # Display NFC reader component
    components.html(nfc_reader_component(), height=150)
    
    # Handle NFC tag reads
    nfc_data = st.empty()
    if st.session_state.nfc_tag:
        nfc_data.info(f"Scanned NFC Tag: {st.session_state.nfc_tag}")
        
        # Determine discipline from NFC tag
        discipline = BLOCK_NFC_QR_MAPPING.get(st.session_state.nfc_tag)
        if discipline:
            st.session_state.discipline = discipline
            st.sidebar.success(f"Detected block: {discipline}")
            
            # Prompt for username and PIN
            username = st.sidebar.text_input("Username")
            pin = st.sidebar.text_input("PIN", type="password")
            
            if st.sidebar.button("Confirm Login"):
                if username and pin:
                    if username not in USER_DB or USER_DB[username] != pin:
                        st.sidebar.error("Invalid credentials")
                    else:
                        st.sidebar.success(f"Welcome {username.capitalize()}!")
                        name = username.capitalize()
                        st.session_state.logged_in = True
                        st.session_state.current_user = name
                        st.session_state.login_time = datetime.now()
                        st.session_state.qr_code = None  # Reset QR code state
        else:
            st.sidebar.error("Unrecognized NFC tag. Please scan a valid block tag.")

else:  # QR Code Login
    st.sidebar.info("Scan QR code at your discipline block to login")
    
    # Display QR code reader component
    components.html(qr_reader_component(), height=200)
    
    # Handle QR code reads
    qr_data = st.empty()
    if st.session_state.qr_code:
        qr_data.info(f"Scanned QR Code: {st.session_state.qr_code}")
        
        # Extract block name from URL
        try:
            # Get the last part of the URL (e.g., 'civil' from 'https://.../civil')
            block_name = st.session_state.qr_code.split('/')[-1].lower()
            mapping_key = f"block_{block_name}"
        except:
            st.sidebar.error("Invalid QR code format")
            block_name = None
            mapping_key = None
        
        # Determine discipline from extracted block name
        if mapping_key:
            discipline = BLOCK_NFC_QR_MAPPING.get(mapping_key)
            if discipline:
                st.session_state.discipline = discipline
                st.sidebar.success(f"Detected block: {discipline}")
                
                # ... rest of your login code remains the same ...
            else:
                st.sidebar.error("Unrecognized block. Please scan a valid block QR code.")

# If not logged in, stop execution
if not st.session_state.get('logged_in', False):
    st.stop()

# ---------- MAIN PAGE ----------
name = st.session_state.current_user
discipline = st.session_state.discipline
st.title(f"📋 Intern Attendance System - Welcome {name}!")

# Display detected discipline
st.success(f"🧭 Block: **{discipline}**")

# ---------- SPECIAL STATUS ----------
status_choice = st.selectbox("Special Status (optional)", ["None", "On Leave", "On Official Duty"])

# ---------- CHECK-IN ----------
if st.button("✅ Check In"):
    status, current_time = perform_check_in(name, discipline, status_choice, st.session_state.login_time)
    st.success(f"Attendance recorded as **{status}** at {current_time}")
    
    # Reset session state after check-in
    st.session_state.nfc_tag = None
    st.session_state.qr_code = None
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.discipline = None
    st.session_state.login_time = None

# ---------- ADMIN VIEW ----------
with st.expander("🔐 Admin Panel"):
    admin_tab = st.tabs(["Attendance Logs"])[0]
    
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

# Listen for NFC and QR code events from JavaScript
components.html("""
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === 'nfcTagRead' || event.data.type === 'qrCodeRead') {
        Streamlit.setComponentValue(event.data.data);
    }
});
</script>
""", height=0)

# Handle NFC/QR code data from JavaScript
nfc_qr_data = components.html("", key="nfc_qr_listener")
if nfc_qr_data:
    if login_method == "NFC":
        st.session_state.nfc_tag = nfc_qr_data
        st.session_state.qr_code = None
    else:
        st.session_state.qr_code = nfc_qr_data
        st.session_state.nfc_tag = None
    st.experimental_rerun()