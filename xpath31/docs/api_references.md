# XPath31 ESRS API Reference

## Core Classes

### XBRLValidator

Main validation engine for XBRL/iXBRL documents.

```python
from xpath31.validator import XBRLValidator

validator = XBRLValidator()
results = validator.validate(filing_content, rules=['UNIT.02', 'SCOPE3.ROLLUP'])