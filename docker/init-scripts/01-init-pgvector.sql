-- Initialize pgvector extension and create memory table
-- This script runs automatically when the PostgreSQL container starts

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create memory table for Mem0 (matching Aurora structure)
CREATE TABLE IF NOT EXISTS mem0_memories (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    memory_text TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_mem0_memories_user_id ON mem0_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_mem0_memories_memory_id ON mem0_memories(memory_id);
CREATE INDEX IF NOT EXISTS idx_mem0_memories_embedding ON mem0_memories 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_mem0_memories_updated_at ON mem0_memories;
CREATE TRIGGER update_mem0_memories_updated_at
    BEFORE UPDATE ON mem0_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify setup
SELECT 'pgvector extension installed' as status, extversion as version 
FROM pg_extension WHERE extname = 'vector';

SELECT 'mem0_memories table created' as status, 
       count(*) as initial_record_count 
FROM mem0_memories;
