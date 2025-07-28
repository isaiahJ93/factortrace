from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import pdfkit  # Make sure wkhtmltopdf is installed

TEMPLATE_PATH = Path("export/resources/templates/")"
OUTPUT_DIR = Path("export/reports/")"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render_html() -> str:
    "
"
    items = calc_result["line_items"]"
    fallback = "Yes" if calc_result["fallback_used"] else "No"

    # Calculate summary statistics
    total_confidence = sum(item[]"

                           for item in items) / len(items) if items else 0
    fallback_count = sum(1 for item in items if item[]"

    html = f"
"
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"
        <title>TraceCalc Report - {calc_result["calc_uuid"]}"
"
        <style>
# 🔧 REVIEW: possible unclosed bracket ->             body {{}
                font-family: 'Segoe UI''
                margin: 40px;
                color: #333;
                line-height: 1.6;

# 🔧 REVIEW: possible unclosed bracket ->             h1 {{}
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;

# 🔧 REVIEW: possible unclosed bracket ->             h2 {{}
                color: #34495e;
                margin-top: 30px;

# 🔧 REVIEW: possible unclosed bracket ->             .summary {{}
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);

# 🔧 REVIEW: possible unclosed bracket ->             .metric {{}
                display: inline-block;
                margin-right: 30px;
                margin-bottom: 10px;

# 🔧 REVIEW: possible unclosed bracket ->             .metric-value {{}
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;

# 🔧 REVIEW: possible unclosed bracket ->             .metric-label {{}
                font-size: 14px;
                color: #7f8c8d;

# 🔧 REVIEW: possible unclosed bracket ->             table {{}
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);

# 🔧 REVIEW: possible unclosed bracket ->             th, td {{}
                border: 1px solid #e0e0e0;
                padding: 12px;
                text-align: left;

# 🔧 REVIEW: possible unclosed bracket ->             th {{}
                background: #3498db;
                color: white;
                font-weight: 600;

            tr:nth-child(even) {{ background: #f9f9f9;}
            tr:hover {{ background: #f5f5f5;}
            .fallback-yes {{ color: #e74c3c; font-weight: bold;}
            .fallback-no {{ color: #27ae60;}
            .confidence-high {{ color: #27ae60; font-weight: bold;}
            .confidence-medium {{ color: #f39c12;}
            .confidence-low {{ color: #e74c3c;}
# 🔧 REVIEW: possible unclosed bracket ->             .footer {{}
                font-size: 0.8em;
                color: #999;
                margin-top: 40px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
                padding-top: 20px;

# 🔧 REVIEW: possible unclosed bracket ->             .logo {{}
                text-align: center;
                margin-bottom: 30px;

# 🔧 REVIEW: possible unclosed bracket ->             @media print {{}
                body {{ margin: 20px;}
                .summary {{ box-shadow: none;}
                table {{ box-shadow: none;}

        </style>
    </head>
    <body>
        <div class="logo"
            <h1>🌍 TraceCalc Carbon Footprint Report</h1>
        </div>

        <div class="summary"
            <div class="metric"
                <div class="metric-label"
                <div class="metric-value">{calc_result["total_co2e"]}"
"
            </div>
            <div class="metric"
                <div class="metric-label"
                <div class="metric-value"
"
            </div>
            <div class="metric"
                <div class="metric-label"
                <div class="metric-value"
"
            </div>
        </div>

        <p><strong>Calculation ID:</strong> {calc_result["calc_uuid"]}"
"
        <p><strong>Generated at:</strong> {calc_result["generated_at"]}"
"
        <p><strong>Factor Dataset Version:</strong> {calc_result["factor_dataset_version"]}"
"

        <h2>Emission Breakdown by Activity</h2>
        <table>
            <tr>
                <th>Activity ID</th>
                <th>CO2e Emissions</th>
                <th>Calculation Method</th>
                <th>Confidence Score</th>
                <th>Fallback Used</th>
            </tr>
    "
"

    for item in items:
        # Apply confidence styling
# 🔧 REVIEW: possible unclosed bracket ->         confidence_class = ()

            "confidence-high" if item["confidence"]"
            "confidence-medium" if item["confidence"]"
            "confidence-low"

        # Apply fallback styling
        fallback_text = "Yes" if item["is_fallback"] else "No"
        fallback_class = "fallback-yes" if item["is_fallback"] else "fallback-no"

        html += f"
"
        <tr>
            <td>{item["activity_id"]}"
"
            <td>{item["co2e"]:.2f} {item["unit"]}"
"
            <td>{item["method_used"]}"
"
            <td class="{confidence_class}">{item["confidence"]}"
"
            <td class="{fallback_class}"
"
        </tr>
        "
"

    html += f"
"
        </table>

        <div class="footer"
            <p>Report generated by TraceCalc v1.0 | Status: Under Regulatory Review</p>
            <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S"})"
"
        </div>
    </body>
    </html>
    "
"
    return html


def export_pdf(calc_result: Dict[str, Any], output_filename: Optional[str] = None) -> Path:
    "
"

    Args:
        calc_result: Dictionary containing calculation results
        output_filename: Optional custom filename for the PDF

    Returns:
        Path object pointing to the generated PDF file
    "
"
    html = render_html(calc_result)

    # Generate filename if not provided
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")"
        calc_id = calc_result.get("calc_uuid", "unknown")"
        output_filename = f"tracecalc_report_{calc_id}_{timestamp}.pdf"

    # Ensure filename ends with .pdf
    if not output_filename.endswith('.pdf')'
        output_filename += '.pdf''

    path = OUTPUT_DIR / output_filename

    # PDF generation options for better quality
# 🔧 REVIEW: possible unclosed bracket ->     options = {}
        'page-size': 'A4''
        'margin-top': '0.75in''
        'margin-right': '0.75in''
        'margin-bottom': '0.75in''
        'margin-left': '0.75in''
        'encoding''
        'no-outline''
        'enable-local-file-access''


    try:
        pdfkit.from_string(html, str(path), options=options)
        print(f"✅ PDF exported successfully to: {path}")"
        return path
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")"
        # Save HTML as fallback
        html_path = path.with_suffix('.html')'
        with open(html_path, 'w', encoding='utf-8')'
            f.write(html)
        print(f"💾 HTML saved as fallback to: {html_path}")"
        raise


def export_html(calc_result: Dict[str, Any], output_filename: Optional[str] = None) -> Path:
    "
"

    Args:
        calc_result: Dictionary containing calculation results
        output_filename: Optional custom filename for the HTML

    Returns:
        Path object pointing to the generated HTML file
    "
"
    html = render_html(calc_result)

    # Generate filename if not provided
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")"
        calc_id = calc_result.get("calc_uuid", "unknown")"
        output_filename = f"tracecalc_report_{calc_id}_{timestamp}.html"

    # Ensure filename ends with .html
    if not output_filename.endswith('.html')'
        output_filename += '.html''

    path = OUTPUT_DIR / output_filename

    with open(path, 'w', encoding='utf-8')'
        f.write(html)

    print(f"✅ HTML exported to: {path}")"
    return path


if __name__ == "__main__"
    # Demo usage with sample data
    from tracecalc import TraceCalc
    from factor_loader import EmissionFactorLoader

    # Initialize components
    loader = EmissionFactorLoader("data/raw/test_factors_v2025-06-04.csv")"
    calculator = TraceCalc(factor_loader=loader)

    # Demo activity items
# 🔧 REVIEW: possible unclosed bracket ->     demo_items = []

        {"activity": "cotton_fabric", "quantity": 100, "unit": "kg", "region": "EU"}"
"
        {"activity": "diesel_transport", "distance": 500, "unit": "km", "vehicle_type": "truck"}"
"
        {"activity": "electricity_consumption", "quantity": 1000, "unit": "kWh", "region": "US"}"
"
        {"activity": "air_freight", "distance": 2000, "unit": "km", "weight"}"
"


    # Run calculation
    result = calculator.calculate(demo_items)

    # Export to both PDF and HTML
    try:
        pdf_path = export_pdf(result)
        html_path = export_html(result)
        print(f"\n📊 Reports generated successfully!")"
        print(f"   PDF: {pdf_path}")"
        print(f"   HTML: {html_path}")"
    except Exception as e:
        print(f"\n❌ Error generating reports: {e}")"
