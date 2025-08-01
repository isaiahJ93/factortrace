# Read main.py
with open('app/main.py', 'r') as f:
    content = f.read()

# Update the except block to show the actual error
content = content.replace(
    'except Exception as e:\n    logger.error(f"❌ Failed to include routers: {e}")',
    '''except Exception as e:
    import traceback
    logger.error(f"❌ Failed to include routers: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")'''
)

# Write back
with open('app/main.py', 'w') as f:
    f.write(content)

print("✅ Updated error logging")
