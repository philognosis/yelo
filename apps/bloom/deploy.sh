#!/bin/bash

# Bloom Production Deployment Script
# Deploys Bloom to production environment

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
echo -e "${BLUE}║         🌸 Bloom Production Deployment Script 🌸          ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    exit 1
fi

# Use 'docker compose' or 'docker-compose' based on what's available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Parse command line arguments
ENVIRONMENT="production"
SKIP_TESTS=false
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --env ENV        Environment (default: production)"
            echo "  --skip-tests     Skip running tests before deploy"
            echo "  --skip-backup    Skip database backup"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Deployment Environment:${NC} ${GREEN}$ENVIRONMENT${NC}"
echo ""

# Pre-deployment checks
echo -e "${BLUE}[1/10] Running pre-deployment checks...${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env from .env.example and configure for production"
    exit 1
fi

# Check critical environment variables
REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "JWT_SECRET"
    "ANTHROPIC_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=your_" .env || grep -q "^${var}=$" .env; then
        echo -e "${RED}❌ Error: ${var} not configured in .env${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Environment configuration valid${NC}"

# Run tests
if [ "$SKIP_TESTS" = false ]; then
    echo -e "${BLUE}[2/10] Running test suite...${NC}"

    if [ -d "tests" ]; then
        # Build test image
        docker build -t bloom-test -f Dockerfile .

        # Run tests
        if docker run --rm bloom-test pytest tests/ -v --cov; then
            echo -e "${GREEN}✓ All tests passed${NC}"
        else
            echo -e "${RED}❌ Tests failed${NC}"
            read -p "Continue deployment anyway? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                echo "Deployment aborted"
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  No tests directory found, skipping tests${NC}"
    fi
else
    echo -e "${YELLOW}[2/10] Skipping tests${NC}"
fi

# Backup database
if [ "$SKIP_BACKUP" = false ]; then
    echo -e "${BLUE}[3/10] Creating database backup...${NC}"

    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/bloom_backup_$(date +%Y%m%d_%H%M%S).sql"

    if docker ps | grep -q bloom-postgres; then
        docker exec bloom-postgres pg_dump -U bloom bloom > "$BACKUP_FILE" || true
        if [ -f "$BACKUP_FILE" ]; then
            echo -e "${GREEN}✓ Database backed up to $BACKUP_FILE${NC}"
        else
            echo -e "${YELLOW}⚠️  Database backup skipped (database not running)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Database not running, skipping backup${NC}"
    fi
else
    echo -e "${YELLOW}[3/10] Skipping database backup${NC}"
fi

# Pull latest code
echo -e "${BLUE}[4/10] Pulling latest changes...${NC}"
if [ -d .git ]; then
    git pull
    echo -e "${GREEN}✓ Code updated${NC}"
else
    echo -e "${YELLOW}⚠️  Not a git repository, skipping pull${NC}"
fi

# Build images
echo -e "${BLUE}[5/10] Building Docker images...${NC}"
$DOCKER_COMPOSE build --no-cache

echo -e "${GREEN}✓ Images built${NC}"

# Stop old containers
echo -e "${BLUE}[6/10] Stopping old containers...${NC}"
$DOCKER_COMPOSE down

echo -e "${GREEN}✓ Old containers stopped${NC}"

# Pull database images
echo -e "${BLUE}[7/10] Pulling database images...${NC}"
$DOCKER_COMPOSE pull postgres redis qdrant

echo -e "${GREEN}✓ Database images updated${NC}"

# Start new containers
echo -e "${BLUE}[8/10] Starting new containers...${NC}"
$DOCKER_COMPOSE up -d --profile full

echo -e "${GREEN}✓ Containers started${NC}"

# Wait for health checks
echo -e "${BLUE}[9/10] Waiting for services to be healthy...${NC}"

RETRY_COUNT=0
MAX_RETRIES=60

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

# Run database migrations (if applicable)
echo -e "${BLUE}[10/10] Running database migrations...${NC}"
# Add your migration commands here if needed
# Example: docker-compose exec api alembic upgrade head

echo -e "${GREEN}✓ Migrations complete${NC}"

# Cleanup old images
echo -e "${BLUE}Cleaning up old images...${NC}"
docker image prune -f

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║         🎉 Deployment Complete! 🎉                         ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Service Status:${NC}"
$DOCKER_COMPOSE ps

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Monitor logs:     ${YELLOW}docker-compose logs -f${NC}"
echo -e "  2. Check metrics:    ${YELLOW}http://localhost:8000/metrics${NC}"
echo -e "  3. Test dashboard:   ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}Deployment to $ENVIRONMENT completed successfully! 🌸${NC}"
