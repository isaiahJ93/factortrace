"""Auto-tagging engine for ESRS concepts."""
import re
from typing import List, Dict, Tuple, Optional
from lxml import etree, html
from decimal import Decimal
from datetime import datetime

from ..taxonomy.taxonomy_loader import ESRSTaxonomyLoader

class AutoTagResult:
    """Result of auto-tagging attempt."""
    def __init__(self, text: str, value: str, concept: str, confidence: float):
        self.text = text
        self.value = value
        self.concept = concept
        self.confidence = confidence
        self.line_number = None
        self.context_ref = None
        self.unit_ref = None

class ESRSAutoTagger:
    """Auto-tag text with ESRS taxonomy concepts."""
    
    # Patterns for finding values
    VALUE_PATTERNS = [
        # Number with thousand separators
        (r'([\d,]+\.?\d*)\s*(thousand|million|billion)?\s*(tonnes?|tCO2e?|kg|EUR|€|\$)?', 'decimal'),
        # Percentage
        (r'(\d+\.?\d*)\s*%', 'percentage'),
        # Currency
        (r'[€$£]\s*([\d,]+\.?\d*)', 'monetary'),
        # Simple number
        (r'(\d+\.?\d*)', 'decimal'),
    ]
    
    def __init__(self, taxonomy_loader: Optional[ESRSTaxonomyLoader] = None):
        """Initialize auto-tagger."""
        self.taxonomy = taxonomy_loader or ESRSTaxonomyLoader()
        self.current_context = "current_period"
        self.current_entity = "reporting_entity"
        
    def auto_tag_document(self, content: str, format: str = 'text') -> List[AutoTagResult]:
        """Auto-tag a document with ESRS concepts."""
        if format == 'html':
            return self._tag_html(content)
        else:
            return self._tag_text(content)
            
    def _tag_text(self, text: str) -> List[AutoTagResult]:
        """Tag plain text content."""
        results = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
                
            # Look for label: value patterns
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    label = parts[0].strip()
                    value_text = parts[1].strip()
                    
                    # Try to find concept
                    concept = self.taxonomy.find_concept_by_label(label)
                    if concept:
                        # Extract numeric value
                        value = self._extract_value(value_text)
                        if value:
                            result = AutoTagResult(
                                text=line,
                                value=value[0],
                                concept=concept,
                                confidence=0.8
                            )
                            result.line_number = line_num + 1
                            result.unit_ref = self._infer_unit(concept, value_text)
                            results.append(result)
                            
        return results
        
    def _tag_html(self, html_content: str) -> List[AutoTagResult]:
        """Tag HTML content."""
        results = []
        doc = html.fromstring(html_content)
        
        # Look for table cells with labels and values
        for row in doc.xpath('//tr'):
            cells = row.xpath('./td')
            if len(cells) >= 2:
                label_cell = cells[0]
                value_cell = cells[1]
                
                label = self._get_text(label_cell).strip()
                value_text = self._get_text(value_cell).strip()
                
                concept = self.taxonomy.find_concept_by_label(label)
                if concept:
                    value = self._extract_value(value_text)
                    if value:
                        result = AutoTagResult(
                            text=f"{label}: {value_text}",
                            value=value[0],
                            concept=concept,
                            confidence=0.9
                        )
                        result.unit_ref = self._infer_unit(concept, value_text)
                        results.append(result)
                        
        # Look for paragraphs with inline values
        for p in doc.xpath('//p'):
            text = self._get_text(p)
            results.extend(self._tag_text(text))
            
        return results
        
    def _extract_value(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract numeric value from text."""
        for pattern, value_type in self.VALUE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                
                # Apply multipliers
                if 'thousand' in text.lower():
                    value = str(float(value) * 1000)
                elif 'million' in text.lower():
                    value = str(float(value) * 1000000)
                elif 'billion' in text.lower():
                    value = str(float(value) * 1000000000)
                    
                return (value, value_type)
                
        return None
        
    def _infer_unit(self, concept: str, text: str) -> str:
        """Infer unit from concept and text."""
        text_lower = text.lower()
        
        # GHG emissions units
        if 'emissions' in concept.lower() or 'ghg' in concept.lower():
            if 'kg' in text_lower:
                return 'kgCO2e'
            elif 'mt' in text_lower or 'megatonne' in text_lower:
                return 'MtCO2e'
            else:
                return 'tCO2e'
                
        # Monetary units
        if any(curr in text_lower for curr in ['€', 'eur', 'euro']):
            return 'EUR'
        elif '$' in text_lower or 'dollar' in text_lower:
            return 'USD'
            
        # Percentage
        if '%' in text:
            return 'pure'
            
        # Count
        if 'number' in concept.lower() or 'count' in concept.lower():
            return 'pure'
            
        return 'pure'  # Default unitless
        
    def _get_text(self, element) -> str:
        """Get text content from HTML element."""
        return ''.join(element.itertext()).strip()
        
    def generate_ixbrl(self, results: List[AutoTagResult], template: str = None) -> str:
        """Generate iXBRL document from tagging results."""
        if not template:
            template = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:esrs-e1="http://www.esrs.eu/taxonomy/e1">
<head>
    <title>ESRS Report</title>
</head>
<body>
    <!-- Auto-tagged content -->
    {content}
</body>
</html>'''
        
        # Generate content
        content_parts = []
        
        # Add units
        units = set(r.unit_ref for r in results if r.unit_ref)
        for unit in units:
            if unit == 'tCO2e':
                content_parts.append('<xbrli:unit id="tCO2e"><xbrli:measure>unit:tCO2e</xbrli:measure></xbrli:unit>')
            elif unit == 'EUR':
                content_parts.append('<xbrli:unit id="EUR"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>')
                
        # Add contexts
        content_parts.append('''<xbrli:context id="current_period">
        <xbrli:entity><xbrli:identifier scheme="http://www.example.com">ENTITY001</xbrli:identifier></xbrli:entity>
        <xbrli:period><xbrli:instant>2024-12-31</xbrli:instant></xbrli:period>
    </xbrli:context>''')
        
        # Add tagged values
        content_parts.append('<div class="auto-tagged">')
        for result in results:
            content_parts.append(f'''
    <p>{result.text.split(":")[0]}: 
        <ix:nonFraction name="{result.concept}" 
                       contextRef="current_period" 
                       unitRef="{result.unit_ref or 'pure'}"
                       decimals="0">{result.value}</ix:nonFraction>
    </p>''')
        content_parts.append('</div>')
        
        return template.format(content='\n    '.join(content_parts))
