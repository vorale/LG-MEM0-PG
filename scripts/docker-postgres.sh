#!/bin/bash

# Docker PostgreSQL Management Script for LangGraph + Mem0 Agent

set -e

CONTAINER_NAME="langgraph-mem0-postgres"
DB_NAME="mem0_agent"
DB_USER="postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|shell|reset|backup|restore}"
    echo ""
    echo "Commands:"
    echo "  start    - Start PostgreSQL container"
    echo "  stop     - Stop PostgreSQL container"
    echo "  restart  - Restart PostgreSQL container"
    echo "  status   - Show container status"
    echo "  logs     - Show container logs"
    echo "  shell    - Connect to PostgreSQL shell"
    echo "  reset    - Reset database (WARNING: deletes all data)"
    echo "  backup   - Create database backup"
    echo "  restore  - Restore database from backup"
}

start_postgres() {
    echo -e "${BLUE}🚀 Starting PostgreSQL container...${NC}"
    
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${YELLOW}⚠️  Container is already running${NC}"
        return 0
    fi
    
    docker-compose -f ../docker/docker-compose.yml up -d
    
    echo -e "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
            echo -e "${GREEN}📊 Connection details:${NC}"
            echo -e "   Host: localhost"
            echo -e "   Port: 5432"
            echo -e "   Database: $DB_NAME"
            echo -e "   User: $DB_USER"
            echo -e "   Password: postgres123"
            return 0
        fi
        sleep 1
        timeout=$((timeout-1))
    done
    
    echo -e "${RED}❌ PostgreSQL failed to start within 30 seconds${NC}"
    return 1
}

stop_postgres() {
    echo -e "${BLUE}🛑 Stopping PostgreSQL container...${NC}"
    docker-compose -f ../docker/docker-compose.yml down
    echo -e "${GREEN}✅ PostgreSQL stopped${NC}"
}

restart_postgres() {
    echo -e "${BLUE}🔄 Restarting PostgreSQL container...${NC}"
    docker-compose -f ../docker/docker-compose.yml restart
    echo -e "${GREEN}✅ PostgreSQL restarted${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Container Status:${NC}"
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${GREEN}✅ Running${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" -f name=$CONTAINER_NAME
    else
        echo -e "${RED}❌ Not running${NC}"
    fi
}

show_logs() {
    echo -e "${BLUE}📝 Container Logs:${NC}"
    docker-compose -f ../docker/docker-compose.yml logs -f postgres
}

connect_shell() {
    echo -e "${BLUE}🐘 Connecting to PostgreSQL shell...${NC}"
    echo -e "${YELLOW}💡 Use \\q to exit${NC}"
    docker exec -it $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME
}

reset_database() {
    echo -e "${RED}⚠️  WARNING: This will delete ALL data in the database!${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🗑️  Resetting database...${NC}"
        docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS mem0_memories CASCADE;"
        docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /docker-entrypoint-initdb.d/01-init-pgvector.sql
        echo -e "${GREEN}✅ Database reset complete${NC}"
    else
        echo -e "${YELLOW}❌ Reset cancelled${NC}"
    fi
}

backup_database() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${BLUE}💾 Creating database backup: $BACKUP_FILE${NC}"
    docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
    echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
}

restore_database() {
    echo -e "${BLUE}📂 Available backup files:${NC}"
    ls -la backup_*.sql 2>/dev/null || echo "No backup files found"
    
    read -p "Enter backup filename: " BACKUP_FILE
    if [ -f "$BACKUP_FILE" ]; then
        echo -e "${BLUE}📥 Restoring from $BACKUP_FILE...${NC}"
        docker exec -i $CONTAINER_NAME psql -U $DB_USER $DB_NAME < $BACKUP_FILE
        echo -e "${GREEN}✅ Database restored${NC}"
    else
        echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    fi
}

# Main script logic
case "$1" in
    start)
        start_postgres
        ;;
    stop)
        stop_postgres
        ;;
    restart)
        restart_postgres
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    shell)
        connect_shell
        ;;
    reset)
        reset_database
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
