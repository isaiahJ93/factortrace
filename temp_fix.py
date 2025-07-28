# Add this to your main.py temporarily
@app.get("/api/v1/emissions")
async def get_emissions():
    return {"emissions": [{"id": "1", "category": "Test", "amount": 0}]}

@app.get("/health")
async def health():
    return {"status": "ok"}
