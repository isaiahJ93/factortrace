with open('factortrace/factor_loader.py', 'r') as f:
    lines = f.readlines()

fixed_lines = []
in_string = False
string_char = None

for i, line in enumerate(lines):
    # Check if line has an unterminated string
    if line.strip() and (
        (line.strip().startswith('"') and line.count('"') % 2 == 1) or
        (line.strip().startswith("'") and line.count("'") % 2 == 1)
    ):
        # Add closing quote
        if '"FIXME' in line or "'FIXME" in line:
            if '"FIXME' in line:
                line = line.rstrip() + '"\n'
            else:
                line = line.rstrip() + "'\n"
            print(f"Fixed line {i+1}: {line.strip()}")
    
    # Check for lone quotes
    if line.strip() == '"' or line.strip() == "'":
        line = line.strip() + line.strip() + '\n'
        print(f"Fixed lone quote on line {i+1}")
    
    fixed_lines.append(line)

with open('factortrace/factor_loader.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed all string issues!")
