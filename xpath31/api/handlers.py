from ..pipeline.orchestrator import process_scope3_filing
from ..builders.scope3_builder import build_scope3_data

@app.post("/api/v1/filings/scope3")
async def create_scope3_filing(request: Request):
    """API endpoint for Scope3 filing submission."""
    data = await request.json()
    
    # Build scope3 data objects
    scope3_objects = build_scope3_data(data)
    
    # Process through pipeline
    result = await process_scope3_filing(
        scope3_objects,
        s3_bucket=os.environ.get("S3_FILING_BUCKET", "xbrl-filings"),
        s3_prefix="filings/scope3/2025"
    )
    
    return JSONResponse(result)