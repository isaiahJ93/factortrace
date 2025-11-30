# CSV Processing Expert

**Trigger**: When working on CSV import, data ingestion, or pandas operations.

**Automatically apply:**
- Use `pd.read_csv()` with explicit `dtype` and `converters`.
- Handle German (1.234,56) and US (1,234.56) formats.
- Sanitize input BEFORE handing to Pint.
- Stream files > 50MB (don't load entirely into memory).
- Return structured errors: `{"row": N, "column": "X", "message": "..."}`.

**Common patterns:**
```python
import pandas as pd

def sanitize_number(s: str) -> str:
    """Detect number format (German vs US) and normalize to '1234.56'."""
    if s is None:
        return ""
    s = str(s).strip()
    if s == "":
        return ""

    # German style: 1.234,56
    if s.count(",") == 1 and s.count(".") > 1:
        return s.replace(".", "").replace(",", ".")

    # US style: 1,234.56 or plain 1234.56
    return s.replace(",", "")

# Safe pandas read
df = pd.read_csv(
    filepath,
    dtype={"activity_value": str},  # Parse manually after sanitization
    converters={"date": pd.to_datetime},
)
```

**Error handling:**
- Never crash on bad data.
- Log errors with context (row, column, value).
- Return actionable error messages for the UI.
