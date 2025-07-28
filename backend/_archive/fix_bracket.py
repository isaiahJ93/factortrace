with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    lines = f.readlines()

# Check line 199
if len(lines) >= 199:
    line_199 = lines[198]  # 0-indexed
    print(f"Line 199: {repr(line_199)}")
    
    # Common issue: extra closing bracket
    if line_199.strip() == ']':
        print("Found lone closing bracket")
        # Check if it should be there
        if len(lines) > 199 and lines[199].strip().startswith('return'):
            # Likely correct, the array ended
            pass
        else:
            # Might be extra
            print("This might be an extra bracket")
    
    # Show context
    print("\nContext:")
    for i in range(max(0, 195), min(len(lines), 205)):
        print(f"{i+1}: {repr(lines[i])}")

# Auto-fix: Remove any standalone ] on line 199 if it's causing issues
if len(lines) >= 199 and lines[198].strip() == ']':
    # Check if the previous line already has a closing bracket
    if len(lines) >= 198 and lines[197].strip().endswith(']'):
        print("\nRemoving extra bracket on line 199")
        lines[198] = ''
        
        with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
            f.writelines(lines)

