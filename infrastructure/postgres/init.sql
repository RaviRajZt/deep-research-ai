-- ============================================
-- Deep Research Platform - PostgreSQL Init Script
-- ============================================
-- Runs on first database initialization only.
-- Creates extensions and sets default configs.
-- ============================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- Trigram similarity for text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";   -- GIN index support

-- Set timezone
SET timezone = 'UTC';

-- Create schemas for logical separation (future use)
CREATE SCHEMA IF NOT EXISTS research;
COMMENT ON SCHEMA research IS 'Research agent data: sessions, results, sources';

CREATE SCHEMA IF NOT EXISTS analytics;
COMMENT ON SCHEMA analytics IS 'Analytics and usage tracking data';
