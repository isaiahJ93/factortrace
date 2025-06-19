from fastapi import FastAPI
from main import app

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "Scope 3 tool online"}

import argparse
from csrd_assistant import run  # ✅ works everywhere now

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Prompt for the CSRD assistant")
    args = parser.parse_args()
    print(run(args.prompt))

if __name__ == "__main__":
    main()

    