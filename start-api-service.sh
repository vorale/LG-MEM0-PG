#!/bin/bash
# Backward compatibility wrapper for the API service startup script

echo "🔄 Redirecting to new script location..."
exec ./scripts/start-api-service.sh "$@"
