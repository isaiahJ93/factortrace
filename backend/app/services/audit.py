from __future__ import annotations


def create_audit_entry(data: dict) -> dict:
    return {
        "event": "Audit Entry Created",
        "data": data,
    }