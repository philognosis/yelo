#!/bin/bash

# Bloom Startup Script
# Starts the Bloom evaluation system with all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║           🌸 Bloom Evaluation System Startup 🌸            ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Error: docker-compose is not installed${NC}"
    echo "Please install docker-compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Use 'docker compose' or 'docker-compose' based on what's available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and configure your settings before proceeding${NC}"
    read -p "Press Enter to continue after configuring .env, or Ctrl+C to exit..."
fi

# Parse command line arguments
PROFILE=""
DETACHED="-d"

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            PROFILE="--profile full"
            shift
            ;;
        --nginx)
            PROFILE="--profile nginx"
            shift
            ;;
        --fg|--foreground)
            DETACHED=""
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full         Start with all optional services (Neo4j, InfluxDB)"
            echo "  --nginx        Start with Nginx reverse proxy"
            echo "  --fg           Run in foreground (don't detach)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Pull latest images
echo -e "${BLUE}[1/5] Pulling Docker images...${NC}"
$DOCKER_COMPOSE pull

# Build application images
echo -e "${BLUE}[2/5] Building Bloom images...${NC}"
$DOCKER_COMPOSE build

# Create necessary directories
echo -e "${BLUE}[3/5] Creating directories...${NC}"
mkdir -p uploads logs

# Start services
echo -e "${BLUE}[4/5] Starting Bloom services...${NC}"
$DOCKER_COMPOSE up $PROFILE $DETACHED

# Wait for services to be healthy
if [ -n "$DETACHED" ]; then
    echo -e "${BLUE}[5/5] Waiting for services to be healthy...${NC}"

    RETRY_COUNT=0
    MAX_RETRIES=30

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ API failed to become healthy${NC}"
        echo "Check logs with: docker-compose logs api"
        exit 1
    fi

    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Dashboard is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Dashboard failed to become healthy${NC}"
        echo "Check logs with: docker-compose logs dashboard"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║              🎉 Bloom is now running! 🎉                   ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  📊 Dashboard:    ${GREEN}http://localhost:3000${NC}"
echo -e "  🔌 API:          ${GREEN}http://localhost:8000${NC}"
echo -e "  📚 API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  🗄️  PostgreSQL:  ${GREEN}localhost:5432${NC}"
echo -e "  🔴 Redis:        ${GREEN}localhost:6379${NC}"
echo -e "  🔍 Qdrant:       ${GREEN}http://localhost:6333${NC}"

if [[ "$PROFILE" == *"full"* ]]; then
    echo -e "  🕸️  Neo4j:       ${GREEN}http://localhost:7474${NC}"
    echo -e "  📈 InfluxDB:     ${GREEN}http://localhost:8086${NC}"
fi

if [[ "$PROFILE" == *"nginx"* ]]; then
    echo -e "  🌐 Nginx:        ${GREEN}http://localhost${NC}"
fi

echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs:       ${YELLOW}docker-compose logs -f${NC}"
echo -e "  Stop services:   ${YELLOW}./stop.sh${NC}"
echo -e "  Restart:         ${YELLOW}docker-compose restart${NC}"
echo -e "  Shell (API):     ${YELLOW}docker-compose exec api bash${NC}"
echo ""
echo -e "${GREEN}Happy evaluating! 🌸${NC}"
