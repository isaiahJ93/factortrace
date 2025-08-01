def smart_fix_indentation(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # First pass: identify function boundaries
    function_starts = []
    for i, line in enumerate(lines):
        if line.strip().startswith('def ') and line.strip().endswith(':'):
            indent = len(line) - len(line.lstrip())
            function_starts.append((i, indent))
    
    # Second pass: fix indentation
    fixed_lines = []
    current_function_indent = 0
    base_content_indent = 4
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if we're starting a new function
        for func_line, func_indent in function_starts:
            if i == func_line:
                current_function_indent = func_indent
                base_content_indent = func_indent + 4
                break
        
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
        else:
            # Determine proper indentation
            if stripped.startswith('def '):
                indent = current_function_indent
            elif stripped.startswith(('if ', 'for ', 'while ', 'try:', 'with ')):
                # These should be at base_content_indent or deeper
                current_indent = len(line) - len(line.lstrip())
                if current_indent < base_content_indent:
                    indent = base_content_indent
                elif current_indent > 20:  # Too deep, probably an error
                    indent = base_content_indent + 8  # Reasonable guess
                else:
                    indent = current_indent
            elif stripped.startswith(('elif ', 'else:', 'except', 'finally:')):
                # Find the matching if/try
                # For now, use a reasonable indent
                current_indent = len(line) - len(line.lstrip())
                if current_indent < base_content_indent:
                    indent = base_content_indent
                else:
                    indent = current_indent
            else:
                # Regular content line
                current_indent = len(line) - len(line.lstrip()) 
                if current_indent == 0 and i > 0:
                    # Probably should be indented
                    indent = base_content_indent
                else:
                    indent = current_indent
            
            fixed_lines.append(' ' * indent + stripped + '\n')
        
        i += 1
    
    # Write the fixed file
    with open(filename, 'w') as f:
        f.writelines(fixed_lines)
    
    print("File has been fixed in place")

# Run the fixer
smart_fix_indentation('app/api/v1/endpoints/esrs_e1_full.py')
