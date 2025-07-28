# Update the Scope3RollupValidationRule class method

def validate(self, document: etree._Element) -> List[ValidationResult]:
    """Check Scope 3 rollup including 15a/b handling with dynamic tolerance."""
    results = []
    namespaces = {
        'ix': 'http://www.xbrl.org/2013/inlineXBRL',
        'xbrli': 'http://www.xbrl.org/2003/instance'
    }
    
    # Collect all Scope 3 values by context
    scope3_by_context = {}
    
    for fact in document.xpath('.//ix:nonFraction', namespaces=namespaces):
        concept = fact.get('name', '')
        context_ref = fact.get('contextRef')
        
        if 'GHGEmissionsScope3' in concept and context_ref:
            try:
                value_text = (fact.text or "").strip().replace(',', '')
                value = Decimal(value_text)
                
                # Apply scale if present
                scale = int(fact.get('scale', '0'))
                if scale != 0:
                    value = value * (Decimal('10') ** scale)
                    
                # Apply sign if present
                if fact.get('sign') == '-':
                    value = -value
                    
                if context_ref not in scope3_by_context:
                    scope3_by_context[context_ref] = {}
                    
                scope3_by_context[context_ref][concept] = value
                
            except (ValueError, InvalidOperation):
                pass
                
    # Check rollups for each context
    for context_ref, values in scope3_by_context.items():
        # Find total concept
        total_concepts = [k for k in values.keys() if 'Total' in k or k.endswith('GHGEmissionsScope3')]
        
        if total_concepts:
            for total_concept in total_concepts:
                reported_total = values[total_concept]
                
                # Sum individual categories
                calculated_total = Decimal('0')
                categories = []
                
                for concept, value in values.items():
                    if concept != total_concept and re.search(r'Cat\d+[ab]?', concept):
                        calculated_total += value
                        categories.append(concept)
                        
                # Special handling for v1.1 with 15a/b
                cat15_values = {}
                for concept in categories:
                    if 'Cat15a' in concept:
                        cat15_values['15a'] = values[concept]
                    elif 'Cat15b' in concept:
                        cat15_values['15b'] = values[concept]
                        
                # If both 15a and 15b present, ensure no double counting
                if len(cat15_values) == 2:
                    # Check if there's also a Cat15 total
                    cat15_total = [c for c in categories if 'Cat15' in c and not ('a' in c or 'b' in c)]
                    if cat15_total:
                        results.append(ValidationResult(
                            rule_id="SCOPE3.15AB",
                            severity="WARNING",
                            message=f"Both Cat15a/b subcategories and Cat15 total found. "
                                    f"Ensure no double-counting in Scope 3 total.",
                            element=total_concept,
                            context={'categories': sorted(categories)}
                        ))
                        
                # Dynamic tolerance: 0.01 or 0.01% of total, whichever is larger
                tolerance = max(Decimal('0.01'), abs(calculated_total) * Decimal('0.0001'))
                
                if abs(reported_total - calculated_total) > tolerance:
                    results.append(ValidationResult(
                        rule_id=self.rule_id,
                        severity="ERROR",
                        message=f"Scope 3 total {total_concept} ({reported_total}) doesn't match "
                                f"sum of categories ({calculated_total}). "
                                f"Difference: {reported_total - calculated_total} "
                                f"(tolerance: ±{tolerance})",
                        element=total_concept,
                        context={
                            'reported_total': str(reported_total),
                            'calculated_total': str(calculated_total),
                            'categories': sorted(categories),
                            'context_ref': context_ref,
                            'tolerance': str(tolerance),
                            'tolerance_type': 'dynamic (0.01 or 0.01%)'
                        }
                    ))
                    
    return results

# Update WhitespaceNormalizationRule to include normalized value in fix suggestion
def validate(self, document: etree._Element) -> List[ValidationResult]:
    """Check for problematic whitespace in numeric values."""
    results = []
    namespaces = {'ix': 'http://www.xbrl.org/2013/inlineXBRL'}
    
    for fact in document.xpath('.//ix:nonFraction | .//ix:fraction', namespaces=namespaces):
        value_text = fact.text or ""
        concept = fact.get('name', 'unnamed')
        
        if not value_text:
            continue
            
        # Use pre-compiled regex for performance
        if self.UNICODE_WHITESPACE_PATTERN.search(value_text):
            # Only do detailed analysis if pattern matches
            found_whitespace = []
            for char, name in self.whitespace_chars.items():
                if char in value_text:
                    found_whitespace.append((char, name))
                    
            if found_whitespace and not (len(found_whitespace) == 1 and found_whitespace[0][0] == '\u0020'):
                # Build detailed message
                details = [f"U+{ord(char):04X} ({name})" for char, name in found_whitespace]
                
                # Create normalized value
                normalized_value = self.UNICODE_WHITESPACE_PATTERN.sub(' ', value_text).strip()
                normalized_value = ' '.join(normalized_value.split())  # Collapse multiple spaces
                
                # Generate fix suggestion
                fix_suggestion = (
                    f'<ix:nonFraction name="{concept}" '
                    f'contextRef="{fact.get("contextRef")}" '
                    f'unitRef="{fact.get("unitRef")}">{normalized_value}</ix:nonFraction>'
                )
                
                results.append(ValidationResult(
                    rule_id=self.rule_id,
                    severity="ERROR",
                    message=f"Fact {concept} contains non-standard whitespace: {', '.join(details)}. "
                            f"Use only standard space (U+0020) or no spaces in numeric values.",
                    element=concept,
                    line=fact.sourceline if hasattr(fact, 'sourceline') else None,
                    context={
                        'value': repr(value_text),  # repr shows escape sequences
                        'whitespace_chars': details,
                        'normalized_value': normalized_value,
                        'fix_suggestion': fix_suggestion
                    }
                ))

                # Add this method to UnitHarmonizationRule class

def generate_auto_fix(self, document: etree._Element) -> Optional[str]:
    """Generate auto-fix XSLT for unit harmonization."""
    results = self.validate(document)
    if not results:
        return None
        
    # Find primary unit from validation results
    primary_unit = None
    conversions = {}
    
    for result in results:
        if result.rule_id == self.rule_id and 'primary_unit' in result.context:
            primary_unit = result.context['primary_unit']
            if 'suggested_value' in result.context:
                conversions[result.element] = {
                    'old_value': result.context.get('value', ''),
                    'new_value': result.context['suggested_value'],
                    'old_unit': result.context.get('unit', ''),
                    'new_unit': primary_unit
                }
                
    if not primary_unit or not conversions:
        return None
        
    # Generate XSLT for auto-fix
    xslt = f"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
    xmlns:xbrli="http://www.xbrl.org/2003/instance">
    
    <xsl:output method="xml" indent="yes"/>
    
    <!-- Identity transform -->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    
    <!-- Update unit references to primary unit -->"""
    
    for concept, conversion in conversions.items():
        xslt += f"""
    <xsl:template match="ix:nonFraction[@name='{concept}']">
        <xsl:copy>
            <xsl:apply-templates select="@*[name()!='unitRef']"/>
            <xsl:attribute name="unitRef">{primary_unit}</xsl:attribute>
            <xsl:text>{conversion['new_value']:.2f}</xsl:text>
        </xsl:copy>
    </xsl:template>"""
    
    xslt += """
</xsl:stylesheet>"""
    
    return xslt

# Update WhitespaceNormalizationRule to add auto-fix
def generate_auto_fix(self, document: etree._Element) -> Optional[str]:
    """Generate auto-fix for whitespace normalization."""
    results = self.validate(document)
    if not results:
        return None
        
    # Generate sed script for auto-fix
    sed_script = "#!/bin/sed -f\n"
    sed_script += "# Auto-fix script for Unicode whitespace normalization\n\n"
    
    # Add replacements for each Unicode whitespace
    for char, name in self.whitespace_chars.items():
        if char != '\u0020':  # Don't replace regular space
            # Convert to octal for sed
            octal = ''.join(f'\\{ord(c):03o}' for c in char.encode('utf-8').decode('latin-1'))
            sed_script += f"# Replace {name} (U+{ord(char):04X})\n"
            sed_script += f"s/{octal}/ /g\n"
            
    # Collapse multiple spaces
    sed_script += "\n# Collapse multiple spaces\n"
    sed_script += "s/  */ /g\n"
    
    return sed_script