#!/bin/bash
# Export iXBRL to PDF format

INPUT_FILE="$1"
OUTPUT_FILE="${2:-output.pdf}"

echo "Converting to PDF..."

# Method 1: Using wkhtmltopdf (if installed)
if command -v wkhtmltopdf &> /dev/null; then
    echo "Using wkhtmltopdf..."
    wkhtmltopdf --enable-local-file-access \
                --margin-top 20mm \
                --margin-bottom 20mm \
                --margin-left 15mm \
                --margin-right 15mm \
                --header-center "ESRS Sustainability Report 2024" \
                --header-font-size 9 \
                --footer-center "[page]" \
                --footer-font-size 9 \
                "$INPUT_FILE" "$OUTPUT_FILE"
    echo "✓ PDF created: $OUTPUT_FILE"
    exit 0
fi

# Method 2: Using Python (weasyprint or pdfkit)
python3 - "$INPUT_FILE" "$OUTPUT_FILE" << 'PYTHON'
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    # Try weasyprint first
    from weasyprint import HTML
    HTML(filename=input_file).write_pdf(output_file)
    print(f"✓ PDF created with weasyprint: {output_file}")
except ImportError:
    try:
        # Try pdfkit
        import pdfkit
        pdfkit.from_file(input_file, output_file)
        print(f"✓ PDF created with pdfkit: {output_file}")
    except ImportError:
        print("❌ Please install PDF converter:")
        print("   pip install weasyprint")
        print("   OR")
        print("   pip install pdfkit")
        print("   OR")
        print("   brew install wkhtmltopdf")
        sys.exit(1)
PYTHON
