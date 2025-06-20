try:
    import pydantic, fastapi, xmlschema
except ImportError as e:
    raise RuntimeError(f"🛑 Missing dependency: {e.name}. Check requirements.txt or install manually.")