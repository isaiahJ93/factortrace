from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Test server is working!"}

@app.get("/api/v1/emission-factors/categories")
def test_categories():
    return {
        "1": ["stationary_combustion", "mobile_combustion"],
        "2": ["electricity"], 
        "3": ["business_travel", "employee_commuting", "waste"]
    }

if __name__ == "__main__":
    print("Starting test server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
