import sys
sys.path.append('.')

from app.main import app

print("All registered routes:")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        print(f"{', '.join(route.methods)}: {route.path}")
