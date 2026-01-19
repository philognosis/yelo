#!/bin/bash

# Bloom Startup Script
# Starts the Bloom evaluation system with all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Please configure your .env file before proceeding${NC}"
    echo -e "${CYAN}Required settings:${NC}"
    echo "  - At least ONE LLM API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY)"
    echo "  - LLM_PROVIDER (anthropic, openai, or gemini)"
    echo ""
    echo -e "${BLUE}Example minimal configuration:${NC}"
    echo "  ANTHROPIC_API_KEY=sk-ant-your-key-here"
    echo "  LLM_PROVIDER=anthropic"
    echo ""
    read -p "Press Enter to continue after configuring .env, or Ctrl+C to exit..."
fi

# Validate critical environment variables
echo -e "${BLUE}[1/6] Validating environment configuration...${NC}"

if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"

    # Check for at least one LLM API key
    if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${RED}❌ Error: No LLM API key found in .env${NC}"
        echo "Please set at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY"
        exit 1
    fi

    # Check LLM_PROVIDER is set
    if [ -z "$LLM_PROVIDER" ]; then
        echo -e "${YELLOW}⚠️  Warning: LLM_PROVIDER not set, defaulting to 'anthropic'${NC}"
    fi

    echo -e "${GREEN}✓ Environment configuration valid${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping validation (no .env file)${NC}"
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

# Navigate to Bloom directory (important for docker-compose context)
cd "$SCRIPT_DIR"

# Pull latest images
echo -e "${BLUE}[2/6] Pulling Docker images...${NC}"
$DOCKER_COMPOSE pull

# Build application images with proper context
echo -e "${BLUE}[3/6] Building Bloom images...${NC}"
echo -e "${CYAN}   Build context: Repository root${NC}"
echo -e "${CYAN}   This allows access to src/iras from apps/bloom${NC}"
$DOCKER_COMPOSE build --no-cache

# Create necessary directories
echo -e "${BLUE}[4/6] Creating directories...${NC}"
mkdir -p uploads logs
echo -e "${GREEN}✓ Directories created${NC}"

# Start services
echo -e "${BLUE}[5/6] Starting Bloom services...${NC}"
$DOCKER_COMPOSE up $PROFILE $DETACHED

# Wait for services to be healthy
if [ -n "$DETACHED" ]; then
    echo -e "${BLUE}[6/6] Waiting for services to be healthy...${NC}"

    RETRY_COUNT=0
    MAX_RETRIES=30

    # Wait for API
    echo -n "   Checking API health..."
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e " ${GREEN}✓ API is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e " ${RED}❌ API failed to become healthy${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  1. Check logs: docker-compose logs api"
        echo "  2. Verify .env configuration"
        echo "  3. Ensure LLM API key is valid"
        exit 1
    fi

    # Wait for Dashboard
    RETRY_COUNT=0
    echo -n "   Checking Dashboard health..."
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e " ${GREEN}✓ Dashboard is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e " ${RED}❌ Dashboard failed to become healthy${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  1. Check logs: docker-compose logs dashboard"
        echo "  2. Verify API is accessible"
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
echo -e "${BLUE}Quick Start:${NC}"
echo -e "  ${CYAN}Run example:${NC}     docker-compose exec api python examples/simple_evaluation.py"
echo -e "  ${CYAN}View logs:${NC}       docker-compose logs -f"
echo -e "  ${CYAN}Stop services:${NC}   ./stop.sh"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  ${CYAN}API shell:${NC}       docker-compose exec api bash"
echo -e "  ${CYAN}Run tests:${NC}       docker-compose exec api pytest tests/ -v"
echo -e "  ${CYAN}Restart:${NC}         docker-compose restart"
echo -e "  ${CYAN}Agent status:${NC}    curl http://localhost:8000/api/v1/swarm/status"
echo ""
echo -e "${GREEN}Happy evaluating! 🌸${NC}"
echo ""
echo -e "${CYAN}💡 Tip: Check out the docs at apps/bloom/docs/LLM_CONFIGURATION.md${NC}"
