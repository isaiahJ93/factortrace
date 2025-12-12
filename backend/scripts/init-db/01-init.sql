-- ==============================================================================
-- FactorTrace Database Initialization Script
-- ==============================================================================
-- This script runs automatically when PostgreSQL container starts
-- Only runs if database is being initialized for the first time
-- ==============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Grant privileges (ensure app user has full access)
GRANT ALL PRIVILEGES ON DATABASE factortrace TO factortrace;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'FactorTrace database initialized successfully at %', NOW();
END $$;
