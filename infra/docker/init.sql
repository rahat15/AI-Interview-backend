-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database if it doesn't exist
-- (This will be handled by docker-compose environment variables)
