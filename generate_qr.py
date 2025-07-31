import qrcode

# Generate QR codes with mapping keys instead of URLs
blocks = ["block_civil", "block_electrical", "block_mechanical"]

for block in blocks:
    qr = qrcode.make(block)
    qr.save(f"{block}_qr.png")

print("✅ QR codes generated for Civil, Electrical, and Mechanical blocks.")