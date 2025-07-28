import re
from pathlib import Path

files = ['src/main.py', 'src/factortrace/compliance_engine.py', 'src/factortrace/factor_loader.py', 'src/factortrace/__init__.py', 'src/factortrace/tracecalc.py', 'src/factortrace/schemas.py', 'src/factortrace/utils.py', 'src/factortrace/voucher_xml_serializer.py', 'src/factortrace/main.py', 'src/factortrace/schema_loader.py', 'src/factortrace/models/common_enums.py', 'src/factortrace/models/uncertainty_model.py', 'src/factortrace/routes/admin.py', 'src/factortrace/services/audit.py', 'src/generator/batch_runner.py', 'src/generator/__init__.py', 'src/generator/xhtml_generator.py', 'src/api/api.py', 'src/api/schemas.py', 'src/export/tracecalc_reporter.py', 'src/routes/report.py', 'tests/test_uncertainty_model.py', 'tests/conftest.py', 'tests/test_serializer.py', 'tests/test_materiality_model.py', 'tests/test_voucher_api.py', 'tests/test_data.py', 'tests/manual_scratch.py', 'tests/data/voucher_sample.py', 'tests/data/sample_data.py']

for file_path in files:
    p = Path(file_path)
    if not p.exists():
        print(f"❌ File not found: {file_path}")
        continue

    with p.open("r") as f:
        lines = f.readlines()

    fixed_lines = []
    open_parens = 0
    for line in lines:
        # Normalize tabs -> 4 spaces
        line = line.replace("\t", "    ")

        # Track parentheses balance
        open_parens += line.count("(") - line.count(")")
        open_parens += line.count("[") - line.count("]")
        open_parens += line.count("{") - line.count("}")

        # Fix illegal annotation lines (e.g., "key": value)
        if re.match(r'\s*"[a-zA-Z0-9_]+":', line):
            fixed_lines.append("    " + line)
        else:
            fixed_lines.append(line)

    # Close unbalanced brackets at end
    if open_parens > 0:
        fixed_lines.append(")" * open_parens + "\n")
    elif open_parens < 0:
        print(f"⚠️  Too many closing brackets in {file_path}")

    # Write back
    with p.open("w") as f:
        f.writelines(fixed_lines)

    print(f"✅ Fixed: {file_path}")