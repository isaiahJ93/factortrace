#!/usr/bin/env python3
"""
Diagnostic tool for ESRS/XBRL report generator.
Identifies structural issues and XBRL compliance problems.
"""
import ast
import re
from pathlib import Path
from collections import defaultdict

def analyze_xbrl_functions(filename):
    """Analyze XBRL-related functions in the file."""
    print("🔍 Analyzing XBRL/ESRS functions...")
    
    xbrl_patterns = {
        'contexts': r'(create|add).*context',
        'facts': r'(create|add).*fact',
        'dimensions': r'(create|add).*dimension',
        'namespaces': r'xmlns:|register_namespace',
        'schemas': r'schemaRef|linkbaseRef',
        'validations': r'validate.*xbrl|check.*compliance',
        'esrs_specific': r'esrs|efrag|e1_|sustainability'
    }
    
    found_patterns = defaultdict(list)
    
    try:
        with open(filename, 'r') as f:
            for i, line in enumerate(f, 1):
                for pattern_name, pattern in xbrl_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        found_patterns[pattern_name].append((i, line.strip()))
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return found_patterns
    
    # Report findings
    for pattern_name, occurrences in found_patterns.items():
        print(f"\n📌 {pattern_name.upper()} ({len(occurrences)} found):")
        for line_no, content in occurrences[:3]:  # Show first 3
            print(f"  Line {line_no}: {content[:80]}...")
    
    return found_patterns

def find_function_boundaries(filename):
    """Find all function definitions and their boundaries."""
    print("\n📊 Mapping function boundaries...")
    
    functions = []
    current_function = None
    indent_stack = []
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            # Check for function definition
            if line.strip().startswith('def '):
                if current_function:
                    current_function['end'] = i
                    functions.append(current_function)
                
                func_match = re.match(r'^(\s*)def\s+(\w+)', line)
                if func_match:
                    indent = len(func_match.group(1))
                    func_name = func_match.group(2)
                    current_function = {
                        'name': func_name,
                        'start': i + 1,
                        'indent': indent,
                        'is_xbrl': any(x in func_name.lower() for x in 
                                     ['xbrl', 'fact', 'context', 'dimension', 'esrs', 'report'])
                    }
        
        # Close last function
        if current_function:
            current_function['end'] = len(lines)
            functions.append(current_function)
    
    except Exception as e:
        print(f"❌ Error analyzing functions: {e}")
        return functions
    
    # Report key functions
    print(f"\n📋 Found {len(functions)} functions")
    xbrl_functions = [f for f in functions if f['is_xbrl']]
    print(f"   - {len(xbrl_functions)} appear to be XBRL/ESRS related")
    
    if xbrl_functions:
        print("\n🎯 Key XBRL/ESRS functions:")
        for func in xbrl_functions[:10]:
            print(f"  {func['name']} (lines {func['start']}-{func['end']})")
    
    return functions

def check_xbrl_requirements(filename):
    """Check for common XBRL/iXBRL requirements."""
    print("\n✅ Checking XBRL compliance requirements...")
    
    requirements = {
        'namespaces': False,
        'contexts': False,
        'units': False,
        'facts': False,
        'schema_ref': False,
        'xhtml_structure': False,
        'utf8_encoding': False
    }
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Check for namespace declarations
        if re.search(r'xmlns:.*=.*"http://.*xbrl', content):
            requirements['namespaces'] = True
        
        # Check for context creation
        if re.search(r'create.*context|Context\(|contextRef', content, re.IGNORECASE):
            requirements['contexts'] = True
        
        # Check for unit handling
        if re.search(r'unit.*=|unitRef|create.*unit', content, re.IGNORECASE):
            requirements['units'] = True
        
        # Check for fact creation
        if re.search(r'create.*fact|add.*fact|ix:.*fraction|ix:.*nonfraction', content, re.IGNORECASE):
            requirements['facts'] = True
        
        # Check for schema reference
        if re.search(r'schemaRef|linkbaseRef', content):
            requirements['schema_ref'] = True
        
        # Check for XHTML structure
        if re.search(r'<!DOCTYPE.*html|<html.*xmlns', content):
            requirements['xhtml_structure'] = True
        
        # Check for UTF-8 handling
        if re.search(r'utf-8|encoding.*=.*["\']utf', content, re.IGNORECASE):
            requirements['utf8_encoding'] = True
    
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
    
    # Report status
    for req, found in requirements.items():
        status = "✅" if found else "❌"
        print(f"  {status} {req.replace('_', ' ').title()}")
    
    missing = [k for k, v in requirements.items() if not v]
    if missing:
        print(f"\n⚠️  Missing {len(missing)} XBRL requirements: {', '.join(missing)}")
    
    return requirements

def suggest_fixes(filename):
    """Suggest specific fixes for common ESRS/XBRL issues."""
    print("\n💡 Suggested fixes for production readiness:")
    
    suggestions = []
    
    # Check for error handling
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Error handling
        if content.count('try:') < 10:
            suggestions.append("Add comprehensive try/except blocks around XBRL generation")
        
        # Logging
        if 'logging' not in content and 'logger' not in content:
            suggestions.append("Implement logging for debugging production issues")
        
        # Validation
        if 'validate' not in content.lower():
            suggestions.append("Add XBRL validation before output")
        
        # Memory efficiency
        if 'ElementTree' in content and 'iterparse' not in content:
            suggestions.append("Consider using iterparse for large XBRL documents")
        
        # Type hints
        if '-> ' not in content:
            suggestions.append("Add type hints for better code maintainability")
    
    except Exception as e:
        print(f"❌ Error analyzing code: {e}")
    
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    else:
        print("  ✅ Code structure looks good!")
    
    return suggestions

def main():
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    if not Path(filename).exists():
        print(f"❌ Error: {filename} not found!")
        return 1
    
    print("=" * 60)
    print("ESRS/XBRL Generator Diagnostic Report")
    print("=" * 60)
    
    # Run diagnostics
    xbrl_patterns = analyze_xbrl_functions(filename)
    functions = find_function_boundaries(filename)
    requirements = check_xbrl_requirements(filename)
    suggestions = suggest_fixes(filename)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Calculate health score
    health_score = 0
    if xbrl_patterns:
        health_score += 25
    if len(functions) > 0:
        health_score += 25
    if sum(requirements.values()) >= 4:
        health_score += 25
    if len(suggestions) <= 2:
        health_score += 25
    
    print(f"\n🏥 Generator Health Score: {health_score}%")
    
    if health_score < 50:
        print("   ⚠️  Critical issues need immediate attention")
    elif health_score < 75:
        print("   🔧 Some improvements needed for production")
    else:
        print("   ✅ Ready for production with minor improvements")
    
    print("\n📋 Next Steps:")
    print("1. Run the indentation fix script first")
    print("2. Ensure all XBRL namespaces are properly declared")
    print("3. Add comprehensive error handling")
    print("4. Validate output against EFRAG technical requirements")
    print("5. Test with sample ESRS data")
    
    return 0

if __name__ == "__main__":
    main()