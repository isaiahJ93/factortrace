import os
import shutil
from pathlib import Path

# List of known broken files from the scan
broken_files = [
    "src/factortrace/compliance_engine.py",
    "src/factortrace/enums.py",
    "src/factortrace/emissions_calculator.py",
    "src/factortrace/factor_loader.py",
    "src/factortrace/shared_enums.py",
    "src/factortrace/__init__.py",
    "src/factortrace/tracecalc.py",
    "src/factortrace/schemas.py",
    "src/factortrace/voucher_types.py",
    "src/factortrace/utils.py",
    "src/factortrace/emissions_voucher.py",
    "src/factortrace/voucher_xml_serializer.py",
    "src/factortrace/main.py",
    "src/factortrace/schema_loader.py",
    "src/factortrace/utils/xml_validation.py",
    "src/factortrace/utils/__init__.py",
    "src/factortrace/utils/coerce.py",
    "src/factortrace/utils/xml_export.py",
    "src/factortrace/models/voucher_generator.py",
    "src/factortrace/models/enums.py",
    "src/factortrace/models/common_enums.py",
    "src/factortrace/models/materiality.py",
    "src/factortrace/models/__init__.py",
    "src/factortrace/models/types.py",
    "src/factortrace/models/uncertainty_model.py",
    "src/factortrace/models/emissions_voucher.py",
    "src/factortrace/models/emissions.py",
    "src/factortrace/models/climate.py",
    "src/factortrace/api/routes_voucher.py",
    "src/factortrace/routes/admin.py",
    "src/factortrace/services/audit.py",
    "src/app/utils/xml_utils.py",
    "src/csrd_assistant/assistant.py",
    "src/cli/generate_report.py",
    "src/generator/batch_runner.py",
    "src/generator/voucher_generator.py",
    "src/generator/retry_failed.py",
    "src/generator/__init__.py",
    "src/generator/xhtml_generator.py",
    "src/generator/arelle_validator.py",
    "src/api/api.py",
    "src/api/schemas.py",
    "src/api/main.py",
    "src/export/tracecalc_reporter.py",
    "src/routes/report.py",
    "tests/test_uncertainty_model.py",
    "tests/test_pass.py",
    "tests/conftest.py",
    "tests/test_xbrl_validation.py",
    "tests/test_vsme_validation.py",
    "tests/test_voucher_model.py",
    "tests/test_serializer.py",
    "tests/__init__.py",
    "tests/test_materiality_model.py",
    "tests/test_voucher_generator.py",
    "tests/test_voucher_api.py",
    "tests/test_data.py",
    "tests/manual_scratch.py",
    "tests/data/voucher_sample.py",
    "tests/data/sample_data.py"
]

backup_dir = Path("broken_backup")
backup_dir.mkdir(parents=True, exist_ok=True)

for file in broken_files:
    src = Path(file)
    dest = backup_dir / src.name
    if src.exists():
        shutil.copy2(src, dest)
        print(f"📦 Backed up: {src} → {dest}")
    else:
        print(f"⚠️ Missing: {src} (skipped)")

print("\n✅ Backup complete.")