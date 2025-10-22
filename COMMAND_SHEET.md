# Claude Code Workshop - Command Sheet

Quick reference for the Natural Language MongoDB Query Interface workshop project.

---

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Custom Slash Commands](#custom-slash-commands)
3. [Development Workflow](#development-workflow)
4. [MCP Server Configuration](#mcp-server-configuration)
5. [Skills](#skills)
6. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### 1. Launch Claude Code
```bash
cd /path/to/workshow-claude
claude
```

### 2. Environment Configuration
```bash
# Create app/server/.env (required)
./.claude/scripts/copy_dot_env.sh
# Edit app/server/.env and add ANTHROPIC_API_KEY

# Create root .env (optional - for hooks, MCP, background agents)
cp .env.sample .env
# Edit .env and add: ANTHROPIC_API_KEY, MDB_MCP_CONNECTION_STRING, FIRECRAWL_API_KEY
```

### 3. Start MongoDB
```bash
./scripts/start_mongodb.sh
```

### 4. Install Dependencies
```bash
# Backend
cd app/server && uv sync --all-extras

# Frontend
cd app/client && npm install
```

### 5. Start the Application
```bash
./scripts/start.sh
```

**Access:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

## Custom Slash Commands

### /start - Launch Application
```
/start
```
Starts both backend and frontend services.

### /feature - Plan New Feature
```
/feature Add export to PDF functionality for query results
```
Creates a detailed feature plan in `specs/feature-<name>.md`.

### /bug - Plan Bug Fix
```
/bug Query results table not rendering when data has special characters
```
Creates a bug fix plan in `specs/bug-<name>.md` with root cause analysis.

### /chore - Plan Maintenance Task
```
/chore Upgrade dependencies and fix deprecation warnings
```
Creates a maintenance plan in `specs/chore-<name>.md`.

### /implement - Execute Plan
```
/implement specs/feature-export-pdf.md
```
Reads and implements the plan step-by-step.

### /background - Run Background Agent
```
/background "Research best practices for MongoDB aggregation performance" sonnet "bg-report.md"
```
Fires up a full Claude Code instance in the background. Saves report to specified file.

### /load_ai_docs - Load Documentation
```
/load_ai_docs
```
Fetches and saves documentation as markdown in `ai_docs/`.

### /prime - Prepare Context
```
/prime
```
Loads project context (README, architecture, key files).

### /tools - List Available Tools
```
/tools
```
Lists all available MCP tools and their capabilities.

### /install - Setup Project
```
/install
```
Complete project setup: dependencies + services.

---

## Development Workflow

### Feature Development Flow

1. **Plan:** `/feature Add data export to CSV functionality`
2. **Review:** Check `specs/feature-export-csv.md`
3. **Implement:** `/implement specs/feature-export-csv.md`
4. **Test:** `cd app/server && uv run pytest`
5. **Commit:** `Create a commit with the changes`
6. **PR:** `Create a pull request`

### Bug Fix Flow

1. **Plan:** `/bug Query fails when collection name has spaces`
2. **Review:** Check `specs/bug-query-spaces.md`
3. **Implement:** `/implement specs/bug-query-spaces.md`
4. **Validate:** `cd app/server && uv run pytest`

---

## MCP Server Configuration

### Atlassian/Jira MCP
```bash
# Add config
claude --mcp-config ".mcp.json.atlassian"

# Set environment
export JIRA_API_TOKEN="your_token"
export JIRA_SITE_URL="https://yourcompany.atlassian.net"
```

Get token: https://id.atlassian.com/manage-profile/security/api-tokens

### Firecrawl MCP (Web Scraping)
Already configured. Check `.claude/settings.local.json` for permissions.

```bash
export FIRECRAWL_API_KEY="your_key"
```

### MongoDB MCP (Optional)
```bash
export MDB_MCP_CONNECTION_STRING="mongodb://admin:admin123@localhost:27017"
```

### Verify MCP Connection
```
Can you list the available MCP tools?
```

---

## Skills

### Jira Ticket Management

**Prerequisites:**
- Atlassian MCP configured: `claude --mcp-config ".mcp.json.atlassian"`
- Environment: `JIRA_API_TOKEN`, `JIRA_SITE_URL`

**Usage:**
```
/skill jira-ticket PROJ-123
/skill jira-ticket PROJ-456 --search-codebase
/skill jira-ticket PROJ-789 --status "In Progress"
```

**Provides:**
- Structured summary (problem, requirements, acceptance criteria)
- Current status and assignee
- Optional codebase search for related files
- Optional status updates

---

## Troubleshooting

### Environment Issues

**App won't start:**
```bash
ls -la app/server/.env
grep ANTHROPIC_API_KEY app/server/.env
```

**Hooks not working:**
```bash
ls -la .env
cat .env
```

### MCP Server Issues

**Server not found:**
```bash
claude --mcp-config ".mcp.json.atlassian"
cat .claude/settings.local.json
```

**Authentication failed:**
```bash
echo $JIRA_API_TOKEN
echo $JIRA_SITE_URL
echo $FIRECRAWL_API_KEY
```

### MongoDB Issues

**Connection failed:**
```bash
docker ps | grep mongo
docker-compose logs mongodb
docker-compose restart mongodb
```

### Dependency Issues

**Backend:**
```bash
cd app/server
rm -rf .venv
uv sync --all-extras
```

**Frontend:**
```bash
cd app/client
rm -rf node_modules
npm install
```

---

## Quick Demo Flow (5 minutes)

1. **Show structure:** `Show me the codebase structure`
2. **Start app:** `/start`
3. **Plan feature:** `/feature Add query history to show the last 10 queries`
4. **Review plan:** Show `specs/feature-query-history.md`
5. **Implement:** `/implement specs/feature-query-history.md`
6. **Show tasks:** Claude automatically tracks progress
7. **MCP demo:** `/skill jira-ticket DEMO-123`

---

## Key Resources

**Configuration:**
- `.claude/settings.json` - Project settings
- `.mcp.json.atlassian` - Atlassian MCP config

**Scripts:**
- `scripts/start.sh` - Start services
- `scripts/start_mongodb.sh` - Start MongoDB
- `.claude/scripts/copy_dot_env.sh` - Setup environment

**Directories:**
- `.claude/commands/` - Custom slash commands
- `.claude/skills/` - MCP orchestration workflows
- `specs/` - Generated plans

---

**Last Updated:** 2025-10-23
