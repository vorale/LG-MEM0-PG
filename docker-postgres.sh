#!/bin/bash

# Wrapper script for docker-postgres.sh in scripts directory
# This provides compatibility with README instructions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

# Check if scripts/docker-postgres.sh exists
if [ ! -f "$SCRIPTS_DIR/docker-postgres.sh" ]; then
    echo "Error: scripts/docker-postgres.sh not found"
    exit 1
fi

# Forward all arguments to the actual script
cd "$SCRIPTS_DIR"
exec ./docker-postgres.sh "$@"
