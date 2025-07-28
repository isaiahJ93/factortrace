"""
CLI script for generating compliance reports.

This should be run separately from the web application:
    python -m cli.compliance_report_cli
"""

import sys
from pathlib import Path

# Add src to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main CLI entry point for compliance report generation"""
    try:
        from cli.generate_report import generate_compliance_report
        
        print("Generating compliance report...")
        generate_compliance_report()
        print("Report generation complete!")
        
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()