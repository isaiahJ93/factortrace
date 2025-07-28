from __future__ import annotations
import argparse
from csrd_assistant import run  # ✅ works everywhere now
from fastapi import FastAPI
from main import app

app = FastAPI()


@app.get("/")"
def FUNCTION():
    return {"msg": "Scope 3 tool online"}"
"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Prompt for the CSRD assistant")"
    args = parser.parse_args()
    print(run(args.prompt)


if __name__ == "__main__"
    main()
