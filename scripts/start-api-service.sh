#!/bin/bash

# LangGraph + Mem0 Agent API Service Startup Script
# This script can be run from the scripts directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting LangGraph + Mem0 Agent API Service"
echo "=============================================="

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📍 Project root: $PROJECT_ROOT"
echo "📍 Script location: $SCRIPT_DIR"

# Change to project root directory
cd "$PROJECT_ROOT"

# Check if we're in the right directory (look for src/api/service.py)
if [ ! -f "src/api/service.py" ]; then
    echo "❌ Error: src/api/service.py not found"
    echo "Please ensure the project structure is correct"
    exit 1
fi

# Check for virtual environment
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

# Check environment variables
echo "🔧 Checking environment configuration..."

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file with your configuration"
    echo "You can copy from .env.local or .env.aurora as a template"
    exit 1
fi

# Source environment variables using a more reliable method
echo "📋 Loading environment variables..."
if [ -f ".env" ]; then
    # Export variables from .env file, ignoring comments and empty lines
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check required environment variables
required_vars=("POSTGRES_HOST" "POSTGRES_PORT" "POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    printf '   - %s\n' "${missing_vars[@]}"
    echo "Please check your .env file"
    exit 1
fi

# Set default values
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}

# Check if PostgreSQL is accessible
echo "🔍 Checking PostgreSQL connection..."
echo "   Database: $POSTGRES_DB"
echo "   Host: $POSTGRES_HOST"
echo "   Port: $POSTGRES_PORT"
echo "   User: $POSTGRES_USER"

python -c "
import psycopg2
import os
import sys

# Print environment variables for debugging
print(f'Environment variables:')
print(f'  POSTGRES_HOST: {os.getenv(\"POSTGRES_HOST\", \"NOT SET\")}')
print(f'  POSTGRES_PORT: {os.getenv(\"POSTGRES_PORT\", \"NOT SET\")}')
print(f'  POSTGRES_USER: {os.getenv(\"POSTGRES_USER\", \"NOT SET\")}')
print(f'  POSTGRES_DB: {os.getenv(\"POSTGRES_DB\", \"NOT SET\")}')

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )
    conn.close()
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('💡 Make sure PostgreSQL is running: ./docker-postgres.sh start')
    sys.exit(1)
" || exit 1

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
python -c "
import boto3
try:
    session = boto3.Session()
    credentials = session.get_credentials()
    if credentials:
        print('✅ AWS credentials found')
    else:
        print('❌ AWS credentials not found')
        print('💡 Please configure AWS credentials: aws configure')
        exit(1)
except Exception as e:
    print(f'❌ AWS credential check failed: {e}')
    exit(1)
" || exit 1

# Test import of main service
echo "🧪 Testing service imports..."
python -c "
try:
    from src.api.service import app
    print('✅ Service imports successful')
except Exception as e:
    print(f'❌ Service import failed: {e}')
    exit(1)
" || exit 1

echo ""
echo "🌐 Starting API server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Workers: $WORKERS"

# Show current emotional companion style
if [ -f ".env" ] && grep -q "EMOTIONAL_COMPANION_STYLE" .env; then
    CURRENT_STYLE=$(grep "EMOTIONAL_COMPANION_STYLE" .env | cut -d'=' -f2)
    echo "   💝 Emotional Style: $CURRENT_STYLE"
elif [ ! -z "$EMOTIONAL_COMPANION_STYLE" ]; then
    echo "   💝 Emotional Style: $EMOTIONAL_COMPANION_STYLE"
else
    echo "   💝 Emotional Style: warm_friend (default)"
fi

echo ""
echo "🎯 API Endpoints:"
echo "   • Chat: http://$HOST:$PORT/v1/chat/completions"
echo "   • Health: http://$HOST:$PORT/health"
echo "   • Info: http://$HOST:$PORT/info"
echo "   • Memory: http://$HOST:$PORT/memory/*"
echo ""
echo "📚 Documentation: http://$HOST:$PORT/docs"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo "=============================================="

# Check if reload mode is requested
if [ -n "$RELOAD" ]; then
    # Development mode with auto-reload
    python -m uvicorn src.api.service:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir src \
        --log-level info
else
    # Production mode
    python -m uvicorn src.api.service:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info
fi
