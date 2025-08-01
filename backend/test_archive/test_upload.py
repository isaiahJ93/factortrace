import os
os.environ['DATABASE_URL'] = 'sqlite:///./factortrace.db'
os.environ['SENTRY_DSN'] = ''

# Now import and run your app
from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
