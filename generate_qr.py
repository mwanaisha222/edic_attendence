import qrcode

# Use localhost for now — update with your deployed URL later
base_url = "https://mwanaisha222-edic-attendence-app-nbfzgp.streamlit.app/"

blocks = ["civil", "electrical", "mechanical"]

for block in blocks:
    full_url = base_url + block
    qr = qrcode.make(full_url)
    qr.save(f"{block}_qr.png")

print("✅ QR codes generated for Civil, Electrical, and Mechanical blocks.")
