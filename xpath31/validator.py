"""XBRL/iXBRL validator for ESRS compliance."""
from typing import List, Dict, Any, Optional
from io import BytesIO
from lxml import etree
import logging

from .compliance.filing_rules import DEFAULT_RULES

logger = logging.getLogger(__name__)

class XBRLValidator:
    """Main validator for XBRL/iXBRL documents."""
    
    def __init__(self):
        """Initialize validator with default rules."""
        self.rules = DEFAULT_RULES
    
    def validate(self, content: bytes, rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate XBRL/iXBRL content."""
        # Parse document
        try:
            doc = etree.parse(BytesIO(content))
        except etree.XMLSyntaxError as e:
            return {
                "validation_results": [{
                    "rule_id": "XML.PARSE",
                    "severity": "ERROR",
                    "message": f"XML parsing error: {e}",
                    "line": e.lineno
                }],
                "statistics": {
                    "total": 1,
                    "errors": 1,
                    "warnings": 0,
                    "info": 0
                },
                "metadata": {
                    "rules_applied": 0,
                    "document_type": "unknown"
                }
            }
        
        results = []
        
        # Apply rules
        for rule in self.rules:
            if rules and rule.rule_id not in rules:
                continue
            try:
                rule_results = rule.validate(doc)
                results.extend(rule_results)
            except Exception as e:
                logger.error(f"Rule {rule.rule_id} failed: {e}")
                results.append({
                    "rule_id": rule.rule_id,
                    "severity": "ERROR",
                    "message": f"Rule execution failed: {e}"
                })
        
        # Convert ValidationResult objects to dicts
        serialized_results = []
        for r in results:
            if hasattr(r, '__dict__'):
                serialized_results.append({
                    "rule_id": r.rule_id,
                    "severity": r.severity,
                    "message": r.message,
                    "element": r.element,
                    "line": r.line,
                    "context": r.context
                })
            else:
                serialized_results.append(r)
        
        # Determine document type
        root = doc.getroot()
        doc_type = "iXBRL" if "inlineXBRL" in str(root.nsmap.values()) else "XBRL"
        
        return {
            "validation_results": serialized_results,
            "statistics": {
                "total": len(serialized_results),
                "errors": sum(1 for r in serialized_results if r.get("severity") == "ERROR"),
                "warnings": sum(1 for r in serialized_results if r.get("severity") == "WARNING"),
                "info": sum(1 for r in serialized_results if r.get("severity") == "INFO")
            },
            "metadata": {
                "rules_applied": len(self.rules),
                "document_type": doc_type
            }
        }
    
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML validation report."""
        html = """
        <html>
        <head>
            <title>XBRL Validation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .error { color: red; }
                .warning { color: orange; }
                .info { color: blue; }
                .summary { background: #f0f0f0; padding: 10px; margin: 10px 0; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>XBRL Validation Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Document Type: {doc_type}</p>
                <p>Total Issues: {total}</p>
                <p>Errors: {errors} | Warnings: {warnings} | Info: {info}</p>
            </div>
            <h2>Validation Results</h2>
            <table>
                <tr>
                    <th>Rule</th>
                    <th>Severity</th>
                    <th>Message</th>
                    <th>Element</th>
                </tr>
        """.format(
            doc_type=results["metadata"]["document_type"],
            total=results["statistics"]["total"],
            errors=results["statistics"]["errors"],
            warnings=results["statistics"]["warnings"],
            info=results["statistics"]["info"]
        )
        
        for result in results["validation_results"]:
            html += """
                <tr>
                    <td>{rule_id}</td>
                    <td class="{severity_class}">{severity}</td>
                    <td>{message}</td>
                    <td>{element}</td>
                </tr>
            """.format(
                rule_id=result.get("rule_id", ""),
                severity=result.get("severity", ""),
                severity_class=result.get("severity", "").lower(),
                message=result.get("message", ""),
                element=result.get("element", "")
            )
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
