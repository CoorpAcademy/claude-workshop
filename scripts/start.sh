#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Natural Language MongoDB Query Interface...${NC}\n"

# Check if .env exists in backend
if [ ! -f "app/server/.env" ]; then
    echo -e "${RED}Error: app/server/.env not found${NC}"
    echo "This file is required for the FastAPI application."
    echo ""
    echo "To create it, run: ./.claude/scripts/copy_dot_env.sh"
    echo "Or manually: cp app/server/.env.sample app/server/.env"
    echo ""
    echo "Then edit app/server/.env and add your ANTHROPIC_API_KEY"
    echo "See README.md 'Environment Configuration' section for details"
    exit 1
fi

echo -e "${GREEN}✓${NC} Application environment file found (app/server/.env)"

# Check for optional workshop features
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}ℹ${NC}  Optional workshop features not configured (root .env missing)"
    echo "   This is OK - the app will run without Claude Code workshop features"
    echo "   To enable hooks/MCP: cp .env.sample .env (see README.md)"
    echo ""
else
    echo -e "${GREEN}✓${NC} Workshop features configured (root .env found)"
fi

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓${NC} Servers stopped"
    exit 0
}

# Set up trap to catch Ctrl+C and other termination signals
trap cleanup SIGINT SIGTERM EXIT

# Start backend
echo -e "\n${GREEN}Starting backend server on http://localhost:8000${NC}"
cd app/server
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# Wait a bit for backend to start
sleep 2

# Start frontend
echo -e "${GREEN}Starting frontend dev server on http://localhost:5173${NC}\n"
cd app/client
npm run dev &
FRONTEND_PID=$!
cd ../..

echo -e "${GREEN}✓${NC} Both servers started!"
echo -e "${GREEN}✓${NC} Backend: http://localhost:8000"
echo -e "${GREEN}✓${NC} Frontend: http://localhost:5173"
echo -e "${GREEN}✓${NC} API Docs: http://localhost:8000/docs"
echo -e "\n${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
