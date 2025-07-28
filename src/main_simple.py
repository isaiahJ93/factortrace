from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FactorTrace API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FactorTrace API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/emissions/calculate")
async def calculate_emissions(data: dict):
    # Mock response
    return {
        "scope1": 0.58,
        "scope2": 0.0,
        "scope3": 0.0,
        "total": 0.58,
        "breakdown": {}
    }

@app.post("/api/reports/generate-elite")
async def generate_elite_report(data: dict):
    return {
        "report_id": "test-123",
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
