from __future__ import annotations
# src/factortrace/services/audit.py

def create_audit_entry(data: dict) -> dict:
    return {
        "event": "Audit Entry Created",
        "data": data
    }