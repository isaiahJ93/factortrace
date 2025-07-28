with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Count brackets
open_brackets = 0
close_brackets = 0
bracket_lines = []

for i, line in enumerate(lines):
    open_count = line.count('[')
    close_count = line.count(']')
    open_brackets += open_count
    close_brackets += close_count
    
    if open_count or close_count:
        bracket_lines.append((i+1, line.strip()[:60], open_count, close_count))

print(f"Total: {open_brackets} '[' and {close_brackets} ']'")
print(f"Mismatch: {open_brackets - close_brackets}")

# Show lines around 199
print("\nLines 190-205:")
for i in range(max(0, 189), min(len(lines), 205)):
    if '[' in lines[i] or ']' in lines[i]:
        print(f"{i+1}: {lines[i]}")

# Find the unmatched bracket
if open_brackets != close_brackets:
    print("\nLooking for the issue...")
    running_count = 0
    for i, line in enumerate(lines):
        running_count += line.count('[') - line.count(']')
        if i >= 195 and i <= 200:
            print(f"Line {i+1}: count={running_count}, {repr(line)}")

