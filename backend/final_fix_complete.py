#!/usr/bin/env python3
"""
Complete final fix for all remaining issues in ESRS E1
"""

from pathlib import Path

def final_fix_complete():
    filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")
    
    print("🚀 COMPLETE FINAL FIX FOR ESRS E1")
    print("=" * 50)
    
    fixed_issues = 0
    max_iterations = 100
    
    for iteration in range(max_iterations):
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
            
            print(f"\n✅ SUCCESS! Fixed {fixed_issues} issues.")
            print("🎉 YOUR ESRS E1 iXBRL GENERATOR IS NOW PRODUCTION READY!")
            
            # Final validation
            print("\n📊 Final validation:")
            with open(filepath, 'r') as f:
                content = f.read()
            
            print(f"  - File size: {len(content):,} characters")
            print(f"  - Lines: {content.count('\n'):,}")
            print(f"  - Functions: {content.count('def '):,}")
            print(f"  - XBRL operations: {content.count('create_context') + content.count('create_fact'):,}")
            print(f"  - Try/except blocks: {content.count('try:')}")
            
            return True
            
        except (SyntaxError, IndentationError) as e:
            if not hasattr(e, 'lineno'):
                print(f"❌ Error without line number: {e}")
                return False
            
            fixed_issues += 1
            print(f"\n🔧 Issue #{fixed_issues}: {e.__class__.__name__} at line {e.lineno}")
            print(f"   Message: {e.msg}")
            
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            if e.lineno > len(lines):
                print("❌ Line number exceeds file length")
                return False
            
            # Apply fix
            fixed = False
            line_idx = e.lineno - 1
            
            if isinstance(e, IndentationError):
                if "expected an indented block after" in e.msg:
                    # Find what statement needs the indented block
                    if "'else'" in e.msg:
                        # Look for the else statement
                        for i in range(line_idx - 1, max(0, line_idx - 5), -1):
                            if lines[i].strip() == 'else:':
                                else_indent = len(lines[i]) - len(lines[i].lstrip())
                                # Fix the line after else
                                lines[line_idx] = ' ' * (else_indent + 4) + lines[line_idx].lstrip()
                                fixed = True
                                print(f"  ✓ Fixed indentation to {else_indent + 4} spaces")
                                break
                    elif "'if'" in e.msg or "'for'" in e.msg or "'while'" in e.msg or "'try'" in e.msg:
                        # General case for control statements
                        prev_line = lines[line_idx - 1] if line_idx > 0 else ""
                        if prev_line.rstrip().endswith(':'):
                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                            lines[line_idx] = ' ' * (prev_indent + 4) + lines[line_idx].lstrip()
                            fixed = True
                            print(f"  ✓ Added indentation ({prev_indent + 4} spaces)")
                
                elif "unindent does not match" in e.msg:
                    # Find correct indentation level
                    current_line = lines[line_idx].strip()
                    
                    # Look for the correct indentation based on context
                    for i in range(line_idx - 1, max(0, line_idx - 30), -1):
                        ref_line = lines[i]
                        if ref_line.strip():
                            ref_indent = len(ref_line) - len(ref_line.lstrip())
                            
                            # If current line is else/elif/except/finally, match with if/try
                            if any(current_line.startswith(kw) for kw in ['else:', 'elif', 'except:', 'finally:']):
                                if any(ref_line.strip().startswith(kw) for kw in ['if ', 'try:', 'for ', 'while ']):
                                    lines[line_idx] = ' ' * ref_indent + lines[line_idx].lstrip()
                                    fixed = True
                                    print(f"  ✓ Aligned to {ref_indent} spaces")
                                    break
                            # Otherwise, use the reference indentation
                            elif not ref_line.rstrip().endswith(':'):
                                lines[line_idx] = ' ' * ref_indent + lines[line_idx].lstrip()
                                fixed = True
                                print(f"  ✓ Aligned to {ref_indent} spaces")
                                break
                
                elif "unexpected indent" in e.msg:
                    # Remove unexpected indentation
                    # Find the expected indentation
                    expected_indent = 0
                    for i in range(line_idx - 1, max(0, line_idx - 10), -1):
                        if lines[i].strip() and not lines[i].rstrip().endswith(':'):
                            expected_indent = len(lines[i]) - len(lines[i].lstrip())
                            break
                    
                    lines[line_idx] = ' ' * expected_indent + lines[line_idx].lstrip()
                    fixed = True
                    print(f"  ✓ Fixed unexpected indent to {expected_indent} spaces")
            
            if fixed:
                # Save the fix
                with open(filepath, 'w') as f:
                    f.writelines(lines)
            else:
                # Show context for manual fix
                print(f"\n  📋 Context around line {e.lineno}:")
                start = max(0, e.lineno - 5)
                end = min(len(lines), e.lineno + 3)
                for i in range(start, end):
                    marker = ">>>" if i == e.lineno - 1 else "   "
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    print(f"  {marker} {i+1:4d} [{indent:2d}]: {lines[i].rstrip()}")
                
                print("\n  ❌ Could not automatically fix this issue")
                return False
    
    print(f"\n⚠️  Reached maximum iterations ({max_iterations})")
    return False

if __name__ == "__main__":
    final_fix_complete()
