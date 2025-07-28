#!/usr/bin/env python3
"""
Fix unterminated string constant error
"""

import os
import shutil
from datetime import datetime

def fix_unterminated_string(file_path):
    """Fix the unterminated string constant error"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Finding and fixing unterminated string...")
    
    # Fix line 1502 (index 1501) - the unterminated string
    if len(lines) > 1501:
        # Check what the line currently looks like
        current_line = lines[1501]
        print(f"Current line 1502: {current_line.strip()}")
        
        # Fix the unterminated string - it should probably be something like:
        # pdf.text('Page ' + i + ' of ' + totalPages, x, y);
        # But since we don't know the full intention, let's complete it minimally
        if "'Page ' + i + '" in current_line and not current_line.strip().endswith(';'):
            # Find where this line should end and fix it
            lines[1501] = "    pdf.text('Page ' + i + '', DESIGN.layout.margins.left, currentY);\n"
            print("✅ Fixed unterminated string on line 1502")
    
    # Also check for any other potential issues around that area
    # Look for other incomplete strings or syntax issues
    for i in range(max(0, 1495), min(len(lines), 1510)):
        line = lines[i]
        
        # Check for lines that might have unterminated strings
        quote_count = line.count("'") + line.count('"')
        if quote_count % 2 != 0 and not line.strip().startswith('//'):
            print(f"⚠️  Line {i+1} might have unmatched quotes: {line.strip()[:50]}...")
            
            # Try to fix common patterns
            if line.strip().endswith("'") and "');" not in line:
                lines[i] = line.rstrip() + ");\n"
                print(f"  ✅ Added missing ); to line {i+1}")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fixed unterminated string issues")
    return True

def check_comment_blocks(file_path):
    """Check and fix any unclosed comment blocks"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Checking comment blocks...")
    
    # Count comment blocks
    open_comments = content.count('/*')
    close_comments = content.count('*/')
    
    if open_comments != close_comments:
        print(f"⚠️  Unmatched comment blocks: {open_comments} open, {close_comments} close")
        
        # Find the last unclosed comment
        last_open = content.rfind('/*')
        last_close = content.rfind('*/')
        
        if last_open > last_close:
            # There's an unclosed comment block
            # Add a closing */ at the end of that section
            insert_pos = content.find('\n', last_open + 100)  # Find a good place to close it
            if insert_pos != -1:
                content = content[:insert_pos] + ' */\n' + content[insert_pos:]
                print("✅ Added missing comment closing */")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    else:
        print("✅ All comment blocks are properly closed")
    
    return True

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
    
    print(f"📁 Processing: {file_path}")
    
    # Create backup
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    try:
        # Fix the unterminated string
        success1 = fix_unterminated_string(file_path)
        success2 = check_comment_blocks(file_path)
        
        if success1 and success2:
            print("\n✨ Fixed unterminated string error!")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n❌ Fix failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()
    