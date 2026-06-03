import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import fpdf

app = FastAPI(title="Villa Karina")

# Mount folders so the browser can access files inside them
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/download", StaticFiles(directory="certificates"), name="download")

RESIDENTS = {"resident_01": {"name": "Jane Doe", "address": "123 Village Lane"}}

class CertificateRequest(BaseModel):
    resident_id: str
    payment_token: str

# ◄--- CHANGED: Now serves the HTML interface instead of JSON text
@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.get("/gallery")
def get_photos():
    return {"images": ["/static/village_square.jpg", "/static/church.jpg"]}

@app.post("/request-certificate")
async def generate_certificate(request: CertificateRequest):
    if request.resident_id not in RESIDENTS:
        raise HTTPException(status_code=404, detail="Residente no registrado")
    
    resident = RESIDENTS[request.resident_id]
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    pdf.cell(200, 10, txt="Certificado Oficial de Domicilio", ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Este Documento Certifica que {resident['name']} habita en {resident['address']}.")
    pdf.ln(20)
    pdf.cell(200, 10, txt="[ Certificado Villa Karina ]", ln=1, align='R')
    
    os.makedirs("certificates", exist_ok=True)
    file_path = f"certificates/{request.resident_id}_cert.pdf"
    pdf.output(file_path)
    
    # Return the URL mapped to our /download static mount
    return {"status": "Success", "download_url": f"/download/{request.resident_id}_cert.pdf"}