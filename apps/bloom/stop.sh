#!/bin/bash

# Bloom Shutdown Script
# Stops all Bloom services

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
echo -e "${BLUE}║           🌸 Bloom Evaluation System Shutdown 🌸           ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Use 'docker compose' or 'docker-compose' based on what's available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Parse command line arguments
REMOVE_VOLUMES=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes|-v)
            REMOVE_VOLUMES="-v"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes  Remove volumes (WARNING: deletes all data)"
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

# Confirm volume removal if requested
if [ -n "$REMOVE_VOLUMES" ]; then
    echo -e "${YELLOW}⚠️  WARNING: This will remove all data volumes!${NC}"
    echo -e "${YELLOW}⚠️  All evaluations, feedback, and database data will be lost.${NC}"
    read -p "Are you sure? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${BLUE}Shutdown cancelled${NC}"
        exit 0
    fi
fi

# Stop services
echo -e "${BLUE}Stopping Bloom services...${NC}"
$DOCKER_COMPOSE down $REMOVE_VOLUMES --remove-orphans

if [ -n "$REMOVE_VOLUMES" ]; then
    echo -e "${GREEN}✓ Services stopped and volumes removed${NC}"
else
    echo -e "${GREEN}✓ Services stopped (volumes preserved)${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║              👋 Bloom has been stopped 👋                  ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -z "$REMOVE_VOLUMES" ]; then
    echo -e "${BLUE}To start again:${NC} ${YELLOW}./start.sh${NC}"
    echo -e "${BLUE}To remove data:${NC} ${YELLOW}./stop.sh --volumes${NC}"
fi
