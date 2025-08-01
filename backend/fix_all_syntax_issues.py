#!/usr/bin/env python3
"""
Fix all syntax issues in the ESRS E1 file
"""

def fix_all_syntax_issues(filepath="app/api/v1/endpoints/esrs_e1_full.py"):
    print("🔧 Fixing all syntax issues...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Fix 1: Line 12001-12002 - add missing indented block
    for i in range(12000, 12005):
        if i < len(lines):
            if 'if not data.get("force_generation", False):' in lines[i] or 'if blocking_issues and not data.get' in lines[i]:
                # Check if next line is properly indented
                if i+1 < len(lines) and not lines[i+1].startswith('        '):
                    print(f"Fixing indentation after if statement at line {i+1}")
                    # The raise ValueError line should be indented
                    if 'raise ValueError' in lines[i+1]:
                        lines[i+1] = '            ' + lines[i+1].strip() + '\n'
    
    # Fix 2: Remove unreachable code after raise (line 12482)
    # The comment after 'raise' should be moved or removed
    for i in range(12478, 12485):
        if i < len(lines):
            if lines[i].strip() == 'raise':
                # Check if there's a comment on the next line at the same indentation
                if i+1 < len(lines) and lines[i+1].strip().startswith('#'):
                    if lines[i+1].startswith('        '):  # Same indentation as raise
                        print(f"Moving comment from line {i+2} (unreachable after raise)")
                        # Remove this line - it's unreachable
                        lines[i+1] = ''
    
    # Fix 3: Fix the head element creation - should be outside try/except
    # The code after except block should be dedented to match the function level
    found_except = False
    for i in range(12475, 12495):
        if i < len(lines):
            if 'except Exception as e:' in lines[i]:
                found_except = True
            elif found_except and lines[i].strip() == 'raise':
                # After this raise, the next non-empty lines should be at function level
                j = i + 1
                while j < len(lines) and j < i + 10:
                    if lines[j].strip():  # Non-empty line
                        if lines[j].startswith('    head = '):
                            print(f"Line {j+1} is already correctly indented")
                        elif 'head = ET.SubElement(root' in lines[j]:
                            print(f"Fixing indentation of head element at line {j+1}")
                            lines[j] = '        ' + lines[j].strip() + '\n'
                        elif 'ET.SubElement(head' in lines[j] and not lines[j].startswith('        '):
                            print(f"Fixing indentation at line {j+1}")
                            lines[j] = '        ' + lines[j].strip() + '\n'
                    j += 1
                break
    
    # Write fixed content
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print("✅ Applied fixes")
    
    # Test syntax
    import subprocess
    result = subprocess.run(['python3', '-m', 'py_compile', filepath], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SYNTAX IS VALID!")
        return True
    else:
        print("❌ Still has errors:")
        if result.stderr:
            # Parse the error to show just the key info
            for line in result.stderr.split('\n'):
                if 'line' in line:
                    print(line)
        return False

if __name__ == "__main__":
    if fix_all_syntax_issues():
        print("\n🎉 Success! Your file is ready.")
        print("\n🧪 Test command:")
        print("""curl -X POST http://localhost:8000/api/v1/esrs-e1/export/esrs-e1-world-class \\
  -H "Content-Type: application/json" \\
  -d @complete_esrs_payload.json | jq -r '.xhtml_content' | grep -c 'ix:nonFraction'""")
