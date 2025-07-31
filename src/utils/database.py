"""
PostgreSQL with pgvector setup script
This script helps you set up PostgreSQL database with pgvector extension
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

def setup_postgres_database():
    """Set up PostgreSQL database with pgvector extension"""
    
    load_dotenv()
    
    # Database configuration for Aurora Serverless
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'database': os.getenv('POSTGRES_DB', 'mem0_agent'),
        'sslmode': os.getenv('POSTGRES_SSL_MODE', 'require'),
        'connect_timeout': int(os.getenv('POSTGRES_CONNECT_TIMEOUT', '30'))
    }
    
    print("🐘 Setting up PostgreSQL database with pgvector")
    print("=" * 50)
    
    try:
        # Connect to PostgreSQL server (without specifying database)
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_config['database']}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {db_config['database']}")
            print(f"✅ Database '{db_config['database']}' created successfully")
        else:
            print(f"✅ Database '{db_config['database']}' already exists")
        
        cursor.close()
        conn.close()
        
        # Connect to the specific database to set up pgvector
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create pgvector extension
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            print("✅ pgvector extension created successfully")
        except Exception as e:
            print(f"⚠️  pgvector extension setup: {e}")
            print("Make sure pgvector is installed on your PostgreSQL server")
        
        # Create memory table for Mem0
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS mem0_memories (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            memory_text TEXT NOT NULL,
            embedding VECTOR(1536),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_mem0_user_id ON mem0_memories(user_id);
        CREATE INDEX IF NOT EXISTS idx_mem0_embedding ON mem0_memories USING ivfflat (embedding vector_cosine_ops);
        """
        
        cursor.execute(create_table_sql)
        print("✅ Memory table created successfully")
        
        cursor.close()
        conn.close()
        
        print("\n✅ PostgreSQL setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL setup failed: {e}")
        return False

def test_postgres_connection():
    """Test PostgreSQL connection"""
    
    load_dotenv()
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'database': os.getenv('POSTGRES_DB', 'mem0_agent')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL connection successful: {version[0]}")
        
        # Test pgvector
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        vector_ext = cursor.fetchone()
        if vector_ext:
            print("✅ pgvector extension is available")
        else:
            print("⚠️  pgvector extension not found")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PostgreSQL + pgvector Setup")
    print("=" * 30)
    
    # Test connection first
    if test_postgres_connection():
        setup_postgres_database()
    else:
        print("\n❌ Please check your PostgreSQL configuration in .env file")
        print("Required environment variables:")
        print("- POSTGRES_HOST")
        print("- POSTGRES_PORT") 
        print("- POSTGRES_USER")
        print("- POSTGRES_PASSWORD")
        print("- POSTGRES_DB")
