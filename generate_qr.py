import qrcode

# Base URL of your Streamlit app
# Replace this with your deployed app URL (e.g., 'https://your-app-name.streamlit.app')
# For local testing, use 'http://localhost:8501'
BASE_URL = "https://mwanaisha222-edic-attendence-main-ndibxo.streamlit.app/"  # Change this to your deployed URL when ready

# Mapping of blocks to query parameter values
blocks = [
    {"key": "block_civil", "discipline": "civil"},
    {"key": "block_electrical", "discipline": "electrical"},
    {"key": "block_mechanical", "discipline": "mechanical"}
]

# Generate QR codes for each block
for block in blocks:
    # Construct the full URL with query parameter
    url = f"{BASE_URL}?block={block['discipline']}"
    
    # Create and save the QR code
    qr = qrcode.make(url)
    qr.save(f"{block['key']}_qr.png")
    print(f"Generated QR code for {block['discipline'].capitalize()} block: {url}")

print("✅ QR codes generated for Civil, Electrical, and Mechanical blocks.")