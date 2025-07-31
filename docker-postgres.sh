#!/bin/bash
# Backward compatibility wrapper for the Docker PostgreSQL management script

echo "🔄 Redirecting to new script location..."
exec ./scripts/docker-postgres.sh "$@"
