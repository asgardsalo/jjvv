import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import fpdf

# --- NEW: Database Libraries ---
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# 1. Database Connection Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/villagedb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Define the Database Table
class ResidentDB(Base):
    __tablename__ = "residents"
    resident_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)

# Create the tables in PostgreSQL automatically when the app starts
Base.metadata.create_all(bind=engine)

# 3. FastAPI App Initialization
app = FastAPI(title="Village Community Board")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/download", StaticFiles(directory="certificates"), name="download")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Pydantic Models for incoming requests
class RegisterRequest(BaseModel):
    resident_id: str
    name: str
    address: str

class CertificateRequest(BaseModel):
    resident_id: str
    payment_token: str

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.get("/gallery")
def get_photos():
    return {"images": ["/static/village_square.jpg", "/static/church.jpg"]}

# NEW: Registration Endpoint
@app.post("/register")
def register_resident(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(ResidentDB).filter(ResidentDB.resident_id == request.resident_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Resident ID already taken.")
    
    # Save new user to PostgreSQL
    new_resident = ResidentDB(
        resident_id=request.resident_id, 
        name=request.name, 
        address=request.address
    )
    db.add(new_resident)
    db.commit()
    return {"status": "Success", "message": "Registration complete!"}

# UPDATED: Certificate Endpoint using the Database
@app.post("/request-certificate")
async def generate_certificate(request: CertificateRequest, db: Session = Depends(get_db)):
    # Look up the resident in PostgreSQL
    resident = db.query(ResidentDB).filter(ResidentDB.resident_id == request.resident_id).first()
    
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found. Please register first.")
    
    # Generate PDF using actual database data
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    pdf.cell(200, 10, txt="OFFICIAL VILLAGE ADDRESS CERTIFICATE", ln=1, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"This is to certify that {resident.name} resides at {resident.address}.")
    pdf.ln(20)
    pdf.cell(200, 10, txt="[ OFFICIAL VILLAGE STAMP ]", ln=1, align='R')
    
    os.makedirs("certificates", exist_ok=True)
    file_path = f"certificates/{request.resident_id}_cert.pdf"
    pdf.output(file_path)
    
    return {"status": "Success", "download_url": f"/download/{request.resident_id}_cert.pdf"}