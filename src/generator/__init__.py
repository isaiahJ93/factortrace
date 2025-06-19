import importlib
importlib.import_module("generator")

def __getattr__(name: str):
    if name == "voucher_generator":                      # ← only the real one
        mod = importlib.import_module(f".{name}", __name__)
        sys.modules[f"{__name__}.{name}"] = mod
        return mod
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r} "
        "(did you mean 'voucher_generator'?)"
    )

# Optional (nice to have): re-export at package level so callers can do
#     from generator import generate_voucher
from .voucher_generator import generate_voucher          # noqa: F401
__all__ = ["voucher_generator", "generate_voucher"]