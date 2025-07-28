import subprocess
import sys

print("Starting FactorTrace Backend on port 8001...")
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8001"])
