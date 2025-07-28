# src/factortrace/utils/zip_utils.py
import zipfile
from pathlib import Path

def create_submission_zip(xhtml_path: Path, pdf_path: Path, output_zip: Path):
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        zipf.write(xhtml_path, arcname="compliance_report.xhtml")
        zipf.write(pdf_path, arcname="supporting_report.pdf")

        