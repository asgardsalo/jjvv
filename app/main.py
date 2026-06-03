from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import fpdf # Used for generating the PDF certificate
import os

app = FastAPI(title="Village Community Board API")

# Mock database for demonstration
RESIDENTS = {"resident_01": {"name": "Jane Doe", "address": "123 Village Lane"}}

class CertificateRequest(BaseModel):
    resident_id: str
    payment_token: str

@app.get("/")
def home():
    return {"message": "Welcome to the Village Community Board!"}

@app.get("/gallery")
def get_photos():
    # In production, pull image URLs from a database or storage bucket
    return {"images": ["/static/village_square.jpg", "/static/church.jpg"]}

@app.post("/request-certificate")
async def generate_certificate(request: CertificateRequest):
    # 1. Verify Resident
    if request.resident_id not in RESIDENTS:
        raise HTTPException(status_code=404, detail="Resident not found or unverified")
    
    # 2. Simulate Bank/Payment Gateway Verification
    # In production, you would use stripe.Charge.retrieve(request.payment_token)
    payment_success = True 
    
    if not payment_success:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    
    # 3. Generate Certificate PDF
    resident = RESIDENTS[request.resident_id]
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    
    # Certificate Header
    pdf.cell(200, 10, txt="OFFICIAL VILLAGE ADDRESS CERTIFICATE", ln=1, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=12)
    cert_text = f"This is to certify that {resident['name']} resides at {resident['address']}."
    pdf.multi_cell(0, 10, cert_text)
    
    # Digital Stamp Placeholder
    pdf.ln(20)
    pdf.cell(200, 10, txt="[ OFFICIAL VILLAGE STAMP - DIGITALLY SIGNED ]", ln=1, align='R')
    
    os.makedirs("certificates", exist_ok=True)
    file_path = f"certificates/{request.resident_id}_cert.pdf"
    pdf.output(file_path)
    
    return {"status": "Success", "download_url": f"/download/{request.resident_id}_cert.pdf"}