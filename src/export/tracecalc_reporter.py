from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import pdfkit  # Make sure wkhtmltopdf is installed

TEMPLATE_PATH = Path("export/resources/templates/")
OUTPUT_DIR = Path("export/reports/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def render_html(calc_result: Dict[str, Any]) -> str:
    """Return a raw HTML report from a CalcResult dictionary."""
    items = calc_result["line_items"]
    fallback = "Yes" if calc_result["fallback_used"] else "No"
    
    # Calculate summary statistics
    total_confidence = sum(item["confidence"] for item in items) / len(items) if items else 0
    fallback_count = sum(1 for item in items if item["is_fallback"])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>TraceCalc Report - {calc_result["calc_uuid"]}</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 40px; 
                color: #333;
                line-height: 1.6;
            }}
            h1 {{ 
                color: #2c3e50; 
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{ 
                color: #34495e; 
                margin-top: 30px;
            }}
            .summary {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .metric {{
                display: inline-block;
                margin-right: 30px;
                margin-bottom: 10px;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .metric-label {{
                font-size: 14px;
                color: #7f8c8d;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 20px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th, td {{ 
                border: 1px solid #e0e0e0; 
                padding: 12px; 
                text-align: left; 
            }}
            th {{ 
                background: #3498db; 
                color: white;
                font-weight: 600;
            }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            tr:hover {{ background: #f5f5f5; }}
            .fallback-yes {{ color: #e74c3c; font-weight: bold; }}
            .fallback-no {{ color: #27ae60; }}
            .confidence-high {{ color: #27ae60; font-weight: bold; }}
            .confidence-medium {{ color: #f39c12; }}
            .confidence-low {{ color: #e74c3c; }}
            .footer {{ 
                font-size: 0.8em; 
                color: #999; 
                margin-top: 40px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
                padding-top: 20px;
            }}
            .logo {{
                text-align: center;
                margin-bottom: 30px;
            }}
            @media print {{
                body {{ margin: 20px; }}
                .summary {{ box-shadow: none; }}
                table {{ box-shadow: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="logo">
            <h1>🌍 TraceCalc Carbon Footprint Report</h1>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-label">Total CO₂e Emissions</div>
                <div class="metric-value">{calc_result["total_co2e"]:,.2f} kg</div>
            </div>
            <div class="metric">
                <div class="metric-label">Average Confidence</div>
                <div class="metric-value">{total_confidence:.1%}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Items with Fallback</div>
                <div class="metric-value">{fallback_count} / {len(items)}</div>
            </div>
        </div>
        
        <p><strong>Calculation ID:</strong> {calc_result["calc_uuid"]}</p>
        <p><strong>Generated at:</strong> {calc_result["generated_at"]}</p>
        <p><strong>Factor Dataset Version:</strong> {calc_result["factor_dataset_version"]}</p>
        
        <h2>Emission Breakdown by Activity</h2>
        <table>
            <tr>
                <th>Activity ID</th>
                <th>CO₂e Emissions</th>
                <th>Calculation Method</th>
                <th>Confidence Score</th>
                <th>Fallback Used</th>
            </tr>
    """
    
    for item in items:
        # Apply confidence styling
        confidence_class = (
            "confidence-high" if item["confidence"] >= 0.8 else
            "confidence-medium" if item["confidence"] >= 0.5 else
            "confidence-low"
        )
        
        # Apply fallback styling
        fallback_text = "Yes" if item["is_fallback"] else "No"
        fallback_class = "fallback-yes" if item["is_fallback"] else "fallback-no"
        
        html += f"""
        <tr>
            <td>{item["activity_id"]}</td>
            <td>{item["co2e"]:.2f} {item["unit"]}</td>
            <td>{item["method_used"]}</td>
            <td class="{confidence_class}">{item["confidence"]:.2%}</td>
            <td class="{fallback_class}">{fallback_text}</td>
        </tr>
        """
    
    html += f"""
        </table>
        
        <div class="footer">
            <p>Report generated by TraceCalc v1.0 | Status: Under Regulatory Review</p>
            <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
        </div>
    </body>
    </html>
    """
    return html


def export_pdf(calc_result: Dict[str, Any], output_filename: Optional[str] = None) -> Path:
    """Export calculation results to PDF format.
    
    Args:
        calc_result: Dictionary containing calculation results
        output_filename: Optional custom filename for the PDF
        
    Returns:
        Path object pointing to the generated PDF file
    """
    html = render_html(calc_result)
    
    # Generate filename if not provided
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        calc_id = calc_result.get("calc_uuid", "unknown")[:8]
        output_filename = f"tracecalc_report_{calc_id}_{timestamp}.pdf"
    
    # Ensure filename ends with .pdf
    if not output_filename.endswith('.pdf'):
        output_filename += '.pdf'
    
    path = OUTPUT_DIR / output_filename
    
    # PDF generation options for better quality
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None
    }
    
    try:
        pdfkit.from_string(html, str(path), options=options)
        print(f"✅ PDF exported successfully to: {path}")
        return path
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        # Save HTML as fallback
        html_path = path.with_suffix('.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 HTML saved as fallback to: {html_path}")
        raise


def export_html(calc_result: Dict[str, Any], output_filename: Optional[str] = None) -> Path:
    """Export calculation results to HTML format.
    
    Args:
        calc_result: Dictionary containing calculation results
        output_filename: Optional custom filename for the HTML
        
    Returns:
        Path object pointing to the generated HTML file
    """
    html = render_html(calc_result)
    
    # Generate filename if not provided
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        calc_id = calc_result.get("calc_uuid", "unknown")[:8]
        output_filename = f"tracecalc_report_{calc_id}_{timestamp}.html"
    
    # Ensure filename ends with .html
    if not output_filename.endswith('.html'):
        output_filename += '.html'
    
    path = OUTPUT_DIR / output_filename
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML exported to: {path}")
    return path


if __name__ == "__main__":
    # Demo usage with sample data
    from tracecalc import TraceCalc
    from factor_loader import EmissionFactorLoader
    
    # Initialize components
    loader = EmissionFactorLoader("data/raw/test_factors_v2025-06-04.csv")
    calculator = TraceCalc(factor_loader=loader)
    
    # Demo activity items
    demo_items = [
        {"activity": "cotton_fabric", "quantity": 100, "unit": "kg", "region": "EU"},
        {"activity": "diesel_transport", "distance": 500, "unit": "km", "vehicle_type": "truck"},
        {"activity": "electricity_consumption", "quantity": 1000, "unit": "kWh", "region": "US"},
        {"activity": "air_freight", "distance": 2000, "unit": "km", "weight": 50}
    ]
    
    # Run calculation
    result = calculator.calculate(demo_items)
    
    # Export to both PDF and HTML
    try:
        pdf_path = export_pdf(result)
        html_path = export_html(result)
        print(f"\n📊 Reports generated successfully!")
        print(f"   PDF: {pdf_path}")
        print(f"   HTML: {html_path}")
    except Exception as e:
        print(f"\n❌ Error generating reports: {e}")