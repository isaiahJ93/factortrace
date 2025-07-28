#!/bin/bash
echo "Starting FactorTrace Backend on port 8001..."
source venv/bin/activate
python -m uvicorn app.main:app --port 8001 --reload
