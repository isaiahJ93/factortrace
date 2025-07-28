#!/usr/bin/env python3
"""
Show the structure of pdf-export-handler.ts and find the right insertion points
"""

import os
import re

def analyze_file_structure(file_path):
    """Analyze and show the file structure with line numbers"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("\n📄 PDF Export Handler Structure Analysis\n")
    print("=" * 80)
    
    # Key patterns to look for
    patterns = {
        'function_start': r'(?:export\s+)?(?:async\s+)?function\s+generatePDFReport',
        'class_start': r'class\s+PDFExportHandler',
        'method_def': r'(?:private|public|protected)\s+(?:async\s+)?(\w+)\s*\([^)]*\)',
        'doc_save': r'doc\.save\(',
        'doc_addpage': r'doc\.addPage\(',
        'autotable': r'doc\.autoTable\(',
        'return_statement': r'return\s+(?:\{|new Promise)',
        'catch_block': r'}\s*catch',
        'class_end': r'^\s*}\s*(?://.*)?$',
        'section_comment': r'//\s*(?:Add|Generate|Create).*section',
        'activity_level': r'Activity-level.*[Dd]ata',
        'footer': r'Footer.*section'
    }
    
    findings = {}
    
    for i, line in enumerate(lines):
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, line):
                if pattern_name not in findings:
                    findings[pattern_name] = []
                findings[pattern_name].append((i + 1, line.strip()[:80]))
    
    # Show findings
    if 'function_start' in findings:
        print("\n📌 Main PDF Generation Function:")
        for line_num, content in findings['function_start']:
            print(f"  Line {line_num}: {content}")
    
    if 'class_start' in findings:
        print("\n📌 PDF Handler Class:")
        for line_num, content in findings['class_start']:
            print(f"  Line {line_num}: {content}")
    
    if 'method_def' in findings:
        print("\n📌 Class Methods Found:")
        for line_num, content in findings['method_def'][:10]:  # Show first 10
            print(f"  Line {line_num}: {content}")
        if len(findings['method_def']) > 10:
            print(f"  ... and {len(findings['method_def']) - 10} more methods")
    
    # Find the main content generation area
    print("\n🔍 Looking for content generation area...")
    
    # Search for specific sections
    content_generation_start = None
    content_generation_end = None
    
    for i, line in enumerate(lines):
        # Look for where main content starts
        if 'Executive Summary' in line or 'ESRS E1' in line:
            if not content_generation_start:
                content_generation_start = i
                print(f"\n✅ Found content generation start at line {i + 1}")
                print(f"   Context: {line.strip()[:80]}")
        
        # Look for where to insert new sections
        if content_generation_start and ('Activity-level' in line or 'Footer' in line or 'doc.save' in line):
            content_generation_end = i
            print(f"\n✅ Found potential insertion point at line {i + 1}")
            print(f"   Context: {line.strip()[:80]}")
            break
    
    # Find where to add new methods
    last_method_line = None
    class_end_line = None
    
    for i in range(len(lines) - 1, 0, -1):
        line = lines[i]
        if re.search(r'^\s*}\s*$', line) and not class_end_line:
            # Check if this is the class closing brace
            # Look for "export" or end of file in next few lines
            for j in range(i + 1, min(i + 5, len(lines))):
                if 'export' in lines[j] or j == len(lines) - 1:
                    class_end_line = i
                    print(f"\n✅ Found class end at line {i + 1}")
                    break
        
        if not last_method_line and re.search(r'^\s*\}\s*$', line):
            # Check if previous lines contain a method
            for j in range(max(0, i - 20), i):
                if re.search(r'(?:private|public|protected)\s+(?:async\s+)?\w+\s*\(', lines[j]):
                    last_method_line = i
                    print(f"\n✅ Found last method end at line {i + 1}")
                    break
            if last_method_line:
                break
    
    # Generate insertion script
    print("\n" + "=" * 80)
    print("\n💡 Insertion Strategy:\n")
    
    if content_generation_end:
        print(f"1. Insert new section calls at line {content_generation_end + 1}")
        print(f"   (After current content, before {lines[content_generation_end].strip()[:40]})")
    
    if last_method_line:
        print(f"\n2. Insert new methods after line {last_method_line + 1}")
        print(f"   (After last method in class)")
    elif class_end_line:
        print(f"\n2. Insert new methods before line {class_end_line + 1}")
        print(f"   (Before class closing brace)")
    
    # Save line numbers for use
    with open('insertion_points.txt', 'w') as f:
        f.write(f"content_insertion_line={content_generation_end + 1 if content_generation_end else 0}\n")
        f.write(f"methods_insertion_line={last_method_line + 1 if last_method_line else (class_end_line if class_end_line else 0)}\n")
    
    print("\n✅ Saved insertion points to insertion_points.txt")
    
    return content_generation_end, last_method_line or class_end_line

def show_context(file_path, line_number, context_lines=5):
    """Show context around a specific line"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)
    
    print(f"\n📋 Context around line {line_number}:")
    print("-" * 80)
    
    for i in range(start, end):
        marker = ">>>" if i == line_number - 1 else "   "
        print(f"{marker} {i + 1:4d}: {lines[i].rstrip()}")
    
    print("-" * 80)

def main():
    """Main function"""
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    current_dir = os.getcwd()
    
    if current_dir != expected_dir:
        try:
            os.chdir(expected_dir)
        except Exception as e:
            print(f"❌ Could not change directory: {e}")
            return
    
    file_path = "./factortrace-frontend/src/components/emissions/pdf-export-handler.ts"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Analyzing: {file_path}")
    
    content_line, methods_line = analyze_file_structure(file_path)
    
    if content_line:
        show_context(file_path, content_line + 1)
    
    if methods_line:
        show_context(file_path, methods_line + 1)
    
    print("\n🚀 Next step: Use the insertion_points.txt file to create a targeted update")

if __name__ == "__main__":
    main()