from setuptools import setup, find_packages

setup(
    name="factortrace-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.111.0",
        "uvicorn[standard]==0.30.0",
        "sqlalchemy==2.0.31",
        "pydantic==2.8.2",
        "pydantic-settings==2.3.0",
        "python-jose[cryptography]==3.3.0",
        "python-multipart==0.0.9",
        "lxml==5.2.0",
        "xmlschema==3.3.0",
        "python-dotenv==1.0.0",
        "httpx==0.27.0",
        "passlib[bcrypt]==1.7.4",
        "alembic==1.13.1",
    ],
)