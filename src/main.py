from fastapi import FastAPI
from contextlib import asynccontextmanager
from factortrace.routes.admin import admin_router
from generator.xhtml_generator import generate_ixbrl
from cli.generate_report import generate_compliance_report
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Sample data for XHTML export
sample_data = {
    "lei": "5493001KJTIIGC8Y1R12",
    "total_emissions": 74295.3
}

# Lifespan handler replacing deprecated @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Startup logic
    for route in app.routes:
        print(f"✅ Route registered: {route.path} [{route.methods}]")
    yield
    # 🛑 Shutdown logic (optional)


# FastAPI app
app = FastAPI(lifespan=lifespan)
app.include_router(admin_router, prefix="/admin")


# CLI + XHTML iXBRL logic
if __name__ == "__main__":
    generate_compliance_report()
    generate_ixbrl(sample_data, "output/report.xhtml")
    print("✅ XHTML iXBRL file generated at output/report.xhtml")

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)

from fastapi import FastAPI
from routes import report  # <-- make sure the path is correct

app = FastAPI()
app.include_router(report.router)
