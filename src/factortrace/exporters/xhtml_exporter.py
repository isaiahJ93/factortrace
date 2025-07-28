from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from factortrace.models.emissions_voucher import EmissionVoucher

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def export_voucher_to_xhtml(voucher: EmissionVoucher, output_path: str) -> None:
    template = env.get_template("voucher_template.xhtml")
    rendered = template.render(voucher=voucher)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)


def generate_ixbrl(voucher, output_path="output/compliance_report.xhtml"):
    env = Environment(loader=FileSystemLoader("src/factortrace/templates"))
    template = env.get_template("ixbrl_template.xhtml")

    rendered = template.render(voucher=voucher)  # Pass entire voucher object to template

    # Ensure output directory exists
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write rendered content to XHTML file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"✅ XHTML report generated at: {output_path}")