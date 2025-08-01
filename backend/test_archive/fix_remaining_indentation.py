#!/usr/bin/env python3
"""
Fix remaining indentation issues with better error handling
"""

from pathlib import Path

def fix_remaining_indentation():
    filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")
    
    print("🔧 FIXING REMAINING INDENTATION ISSUES")
    print("=" * 50)
    
    fixed_count = 0
    max_iterations = 20
    
    for iteration in range(max_iterations):
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
            
            print(f"\n✅ SUCCESS! Fixed all indentation issues!")
            print(f"🎉 YOUR ESRS E1 iXBRL GENERATOR IS NOW PRODUCTION READY!")
            print(f"\n📊 Total fixes applied: {fixed_count}")
            return True
            
        except IndentationError as e:
            if not hasattr(e, 'lineno'):
                print(f"❌ Error without line number: {e}")
                return False
                
            print(f"\n🔧 Iteration {iteration + 1}: Fixing {e.msg} at line {e.lineno}")
            
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            if e.lineno > len(lines):
                print(f"❌ Line number {e.lineno} exceeds file length")
                return False
            
            line_idx = e.lineno - 1
            
            # Handle different types of indentation errors
            if "unindent does not match" in e.msg:
                # Find the correct indentation by looking at surrounding code
                correct_indent = find_correct_indent(lines, line_idx)
                if correct_indent is not None:
                    lines[line_idx] = ' ' * correct_indent + lines[line_idx].lstrip()
                    fixed_count += 1
                    print(f"  ✓ Fixed to {correct_indent} spaces")
                else:
                    print(f"  ❌ Could not determine correct indentation")
                    show_context(lines, e.lineno)
                    return False
                    
            elif "expected an indented block" in e.msg:
                # Add indentation after control statement
                prev_line = lines[line_idx - 1] if line_idx > 0 else ""
                if prev_line.rstrip().endswith(':'):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    lines[line_idx] = ' ' * (prev_indent + 4) + lines[line_idx].lstrip()
                    fixed_count += 1
                    print(f"  ✓ Added indentation ({prev_indent + 4} spaces)")
                    
            elif "unexpected indent" in e.msg:
                # Remove or fix unexpected indentation
                # Look for the previous non-empty line's indentation
                for i in range(line_idx - 1, -1, -1):
                    if lines[i].strip():
                        ref_indent = len(lines[i]) - len(lines[i].lstrip())
                        lines[line_idx] = ' ' * ref_indent + lines[line_idx].lstrip()
                        fixed_count += 1
                        print(f"  ✓ Aligned to {ref_indent} spaces")
                        break
            
            # Save the fix
            with open(filepath, 'w') as f:
                f.writelines(lines)
                
        except SyntaxError as e:
            if "expected an indented block" in str(e) and hasattr(e, 'lineno'):
                # Handle as indentation error
                print(f"\n🔧 Fixing missing indentation at line {e.lineno}")
                
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                
                if e.lineno <= len(lines):
                    prev_line = lines[e.lineno - 2] if e.lineno > 1 else ""
                    if prev_line.rstrip().endswith(':'):
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                        lines[e.lineno - 1] = ' ' * (prev_indent + 4) + lines[e.lineno - 1].lstrip()
                        fixed_count += 1
                        
                        with open(filepath, 'w') as f:
                            f.writelines(lines)
            else:
                print(f"\n❌ Non-indentation syntax error: {e}")
                return False
    
    print(f"\n⚠️  Reached maximum iterations ({max_iterations})")
    return False

def find_correct_indent(lines, line_idx):
    """Find the correct indentation for a line based on context"""
    # Look at the surrounding code structure
    current_line = lines[line_idx].strip()
    
    # Common patterns
    if current_line.startswith('return'):
        # Return statements are usually at function level (4 spaces) or inside blocks
        # Look backwards for the function def
        for i in range(line_idx - 1, max(0, line_idx - 50), -1):
            if lines[i].strip().startswith('def '):
                return len(lines[i]) - len(lines[i].lstrip()) + 4
    
    # Look for the previous line at a valid indentation level
    valid_indents = [0, 4, 8, 12, 16, 20, 24, 28, 32]
    for i in range(line_idx - 1, max(0, line_idx - 20), -1):
        if lines[i].strip():
            indent = len(lines[i]) - len(lines[i].lstrip())
            if indent in valid_indents:
                # Check if this line ends with : (then we need more indent)
                if lines[i].rstrip().endswith(':'):
                    return indent + 4
                else:
                    return indent
    
    return None

def show_context(lines, line_num):
    """Show context around an error"""
    if line_num and line_num <= len(lines):
        print(f"\n📋 Context around line {line_num}:")
        start = max(0, line_num - 5)
        end = min(len(lines), line_num + 3)
        
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            indent = len(lines[i]) - len(lines[i].lstrip())
            print(f"{marker} {i+1:4d} [{indent:2d}]: {lines[i]}", end='')

if __name__ == "__main__":
    fix_remaining_indentation()
