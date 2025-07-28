from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FactorTrace API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FactorTrace API is running!"}

@app.get("/api/emissions")
def get_emissions():
    return [
        {"id": 1, "scope": 1, "amount": 234.5, "unit": "tCO2e", "category": "Direct"},
        {"id": 2, "scope": 2, "amount": 156.2, "unit": "tCO2e", "category": "Energy"},
        {"id": 3, "scope": 3, "amount": 856.6, "unit": "tCO2e", "category": "Value Chain"},
    ]

@app.post("/api/vouchers/create")
def create_voucher(data: dict):
    return {"id": "123", "status": "created", "data": data}

@app.post("/api/xbrl/generate")
def generate_xbrl(data: dict):
    return {"status": "success", "xbrl": "<xbrl>...</xbrl>"}
