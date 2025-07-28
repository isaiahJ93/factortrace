#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Setting up PostgreSQL for FactorTrace..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed. Please install it first.${NC}"
    echo "On macOS: brew install postgresql"
    exit 1
fi

# Start PostgreSQL if not running
if ! pg_isready &> /dev/null; then
    echo "Starting PostgreSQL..."
    if command -v brew &> /dev/null; then
        brew services start postgresql
    else
        sudo systemctl start postgresql
    fi
    sleep 2
fi

# Database configuration
DB_USER="factortrace"
DB_PASSWORD="factortrace_password"
DB_NAME="factortrace_db"

# Create user and database
echo "Creating database and user..."
psql -U postgres << EOF
-- Create user if not exists
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '${DB_USER}') THEN
      CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
   END IF;
END
\$do\$;

-- Create database if not exists
SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# Application
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=development
DEBUG=true

# GHG Calculator Settings
ENABLE_UNCERTAINTY=true
MONTE_CARLO_ITERATIONS=10000
ENABLE_EXTERNAL_PROVIDERS=true
EOF
    echo -e "${GREEN}.env file created${NC}"
else
    echo ".env file already exists. Updating DATABASE_URL..."
    # Update DATABASE_URL in existing .env
    if grep -q "DATABASE_URL" .env; then
        sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}|" .env
    else
        echo "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}" >> .env
    fi
fi

echo -e "${GREEN}PostgreSQL setup complete!${NC}"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"