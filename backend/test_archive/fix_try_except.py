# Read the file
with open('app/main.py', 'r') as f:
    content = f.read()

# Find the incomplete try-except block and fix it
import re

# Fix the pattern where except line is incomplete
content = re.sub(
    r'(logger\.info\("✅ Emissions and Voucher routers manually included"\)\s*\n)except Exception as e:',
    r'\1except Exception as e:\n    logger.error(f"❌ Failed to include routers: {e}")',
    content
)

# Write back
with open('app/main.py', 'w') as f:
    f.write(content)

print("✅ Fixed try-except block")
