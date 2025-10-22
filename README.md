# Natural Language MongoDB Query Interface

A web application that converts natural language queries to MongoDB queries using AI, built with FastAPI and Vite + TypeScript.

## Features

- 🗣️ Natural language to MongoDB query conversion using Claude (Anthropic)
- 📁 Drag-and-drop file upload (.csv and .json)
- 📊 Interactive table results display
- ⚡ Fast development with Vite and uv

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose (for MongoDB)
- Anthropic API key (for Claude)
- astral uv (Python package manager)

## Environment Configuration

This project uses **two separate `.env` files** for different purposes:

### Required: Application Configuration (`app/server/.env`)

The FastAPI application requires configuration in `app/server/.env`:

```bash
cd app/server
cp .env.sample .env
# Edit .env and add your API keys
```

**Required variables:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude AI ([Get one here](https://console.anthropic.com/))
- `MONGODB_URI` - MongoDB connection string (default: `mongodb://admin:admin123@localhost:27017`)
- `MONGODB_DATABASE` - Database name (default: `nlq_interface`)

**This file is required to run the application.** The FastAPI server loads these variables via `python-dotenv`.

### Optional: Workshop Features (`.env` in project root)

The Claude Code workshop infrastructure uses a separate `.env` file in the project root for:
- Claude Code hooks (automation scripts in `.claude/hooks/`)
- MCP server integrations (MongoDB MCP, Firecrawl)
- Background agent execution (E2B)
- GitHub integrations

```bash
cp .env.sample .env
# Edit .env and add optional workshop API keys
```

**Optional variables:**
- `ANTHROPIC_API_KEY` - For Claude Code hooks and MCP integrations
- `MDB_MCP_CONNECTION_STRING` - MongoDB connection for MCP server
- `FIRECRAWL_API_KEY` - For web scraping MCP integration
- `E2B_API_KEY` - For cloud sandbox agent execution
- `GITHUB_PAT` - For GitHub workflow automation examples

**This file is optional.** You only need it if you want to use the advanced Claude Code workshop features like hooks and MCP integrations. The application will run fine without it.

### Quick Setup

For a **minimal setup** (just run the app):
```bash
./.claude/scripts/copy_dot_env.sh
# This creates app/server/.env - edit it to add your ANTHROPIC_API_KEY
```

For **full workshop** (app + Claude Code features):
```bash
./.claude/scripts/copy_dot_env.sh  # Creates app/server/.env
cp .env.sample .env                 # Creates root .env
# Edit both files to add your API keys
```

### Troubleshooting Environment Files

- **"Application won't start"** → Check that `app/server/.env` exists and has valid `ANTHROPIC_API_KEY`
- **"Claude Code hooks not working"** → Check that root `.env` exists and has valid keys for MCP/hooks
- **"Which .env file for what?"** → `app/server/.env` is for the app, root `.env` is for Claude Code features
- **"Can I use the same API key?"** → Yes, you can set the same `ANTHROPIC_API_KEY` in both files if using both

## Setup

### 1. Start MongoDB

Start the MongoDB container using Docker Compose:

```bash
./scripts/start_mongodb.sh
```

Or manually:

```bash
docker-compose up -d
```

This will start MongoDB on `localhost:27017`.

### 2. Environment Configuration

Follow the [Environment Configuration](#environment-configuration) section above to set up your `.env` files.

### 3. Install Dependencies

```bash
# Backend
cd app/server
uv sync --all-extras

# Frontend
cd app/client
npm install
```

## Quick Start

Use the provided script to start both services:

```bash
./scripts/start.sh
```

Press `Ctrl+C` to stop both services.

The script will:
- Check that `.env` exists in `app/server/`
- Start the backend on http://localhost:8000
- Start the frontend on http://localhost:5173
- Handle graceful shutdown when you exit

## Manual Start (Alternative)

### Backend
```bash
cd app/server
# .env is loaded automatically by python-dotenv
uv run python server.py
```

### Frontend
```bash
cd app/client
npm run dev
```

## Usage

1. **Upload Data**: Click "Upload Data" to open the modal
   - Use sample data buttons for quick testing
   - Or drag and drop your own .csv or .json files
   - Uploading a file with the same name will overwrite the existing collection
2. **Query Your Data**: Type a natural language query like "Show me all users who signed up last week"
   - Press `Cmd+Enter` (Mac) or `Ctrl+Enter` (Windows/Linux) to run the query
3. **View Results**: See the generated MongoDB queries and results in a table format
4. **Manage Collections**: Click the × button on any collection to remove it

## Development

### Backend Commands
```bash
cd app/server
uv run python server.py      # Start server with hot reload
uv run pytest               # Run tests
uv add <package>            # Add package to project
uv remove <package>         # Remove package from project
uv sync --all-extras        # Sync all extras
```

### Frontend Commands
```bash
cd app/client
npm run dev                 # Start dev server
npm run build              # Build for production
npm run preview            # Preview production build
```

## Project Structure

```
.
├── app/                    # Main application
│   ├── client/             # Vite + TypeScript frontend
│   └── server/             # FastAPI backend
│
├── .claude/                # Claude Code configuration
│   ├── commands/           # Custom slash commands
│   └── scripts/            # Automation scripts
│
├── scripts/                # Utility scripts (start.sh, start_mongodb.sh)
├── specs/                  # Feature specifications
└── ai_docs/                # AI/LLM documentation (optional)
```

## Claude Code Workshop

This project is designed as a workshop to teach Claude Code capabilities:

- **Slash Commands**: Custom commands in `.claude/commands/` (e.g., `/start`, `/bug`, `/feature`)
- **Agents & Subagents**: Background task execution and code exploration
- **Hooks System**: Automated workflows triggered by events
- **MCP Integrations**: Model Context Protocol for extended capabilities
- **Skills**: Reusable workflows for Jira and Figma integration
- **MongoDB NL Query App**: Practical example application for demonstrations

## Claude Code Skills

This project includes two powerful skills that demonstrate MCP (Model Context Protocol) orchestration for integrating external tools into your development workflow.

### Jira Ticket Management Skill

Intelligently read Jira tickets, understand requirements, and optionally update ticket status with context-aware automation.

**Purpose**: Bridge Jira project management with your codebase for seamless requirement tracking and status synchronization.

**Prerequisites**:
- Atlassian MCP server configured (`.mcp.json.atlassian`)
- Jira API authentication set up
- Environment variables:
  ```bash
  export JIRA_API_TOKEN="your_api_token_here"
  export JIRA_SITE_URL="https://yourcompany.atlassian.net"
  ```

**Usage Examples**:

1. **Read a Jira ticket**:
   ```bash
   /skill jira-ticket PROJ-456
   ```
   Output: Structured summary with problem statement, requirements, acceptance criteria, and current status.

2. **Read ticket and search codebase**:
   ```bash
   /skill jira-ticket WORK-789 --search-codebase
   ```
   Output: Ticket summary + related files in your codebase.

3. **Read and update status**:
   ```bash
   /skill jira-ticket PROJ-123 --status "In Progress"
   ```
   Output: Ticket summary + confirmation of status transition.

**What it does**:
- Fetches ticket details (summary, description, acceptance criteria, status, assignee)
- Extracts key requirements and technical specifications
- Generates developer-friendly summary
- Optionally searches codebase for related files
- Optionally updates ticket status with valid transitions

### Figma Design QA Skill

Fetch Figma component designs, compare with code implementation, and generate comprehensive design-to-implementation comparison reports.

**Purpose**: Ensure design fidelity by systematically identifying discrepancies between Figma designs and actual code.

**Prerequisites**:
- Figma MCP server configured (global or project `.mcp.json`)
- Figma personal access token
- Environment variable:
  ```bash
  export FIGMA_ACCESS_TOKEN="your_figma_token_here"
  ```
- Get your token at: https://www.figma.com/developers/api#access-tokens

**Usage Examples**:

1. **Basic component QA**:
   ```bash
   /skill design-qa Button src/components/Button.tsx
   ```
   Output: Full QA report comparing Figma Button design with implementation.

2. **Specific variant QA**:
   ```bash
   /skill design-qa Button:primary src/components/Button.tsx --variant primary
   ```
   Output: QA report focused on the "primary" variant.

3. **Color-focused QA**:
   ```bash
   /skill design-qa Card src/components/Card.tsx --focus colors
   ```
   Output: QA report emphasizing color comparisons (useful for theme migration).

4. **Responsive component QA**:
   ```bash
   /skill design-qa Header src/components/Header.tsx --focus responsive
   ```
   Output: Analysis of responsive behavior across breakpoints.

**What it does**:
- Fetches Figma design specifications (dimensions, colors, typography, spacing, layout)
- Reads and parses implementation code
- Performs systematic comparison across all visual properties
- Identifies discrepancies categorized by severity (critical, high, medium, low)
- Generates actionable QA report with:
  - Design fidelity score
  - Detailed comparison of design specs vs code
  - List of discrepancies with specific fix recommendations
  - Code snippets showing before/after
  - Validation checklist for verification

### MCP Server Setup

#### Atlassian/Jira MCP Server

The Atlassian MCP server configuration is available in `.mcp.json.atlassian`:

```json
{
  "mcpServers": {
    "atlassian": {
      "type": "sse",
      "url": "https://mcp.atlassian.com/v1/sse"
    }
  }
}
```

**Authentication Setup**:
1. Generate a Jira API token:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Give it a label (e.g., "Claude Code MCP")
   - Copy the token

2. Set environment variables:
   ```bash
   export JIRA_API_TOKEN="your_api_token_here"
   export JIRA_SITE_URL="https://yourcompany.atlassian.net"
   ```

3. Test connectivity:
   ```bash
   # Try using the jira-ticket skill with a valid ticket ID
   /skill jira-ticket PROJ-123
   ```

#### Figma MCP Server

The Figma MCP server should be configured in your global MCP config (`~/.mcp.json`) or project-specific `.mcp.json`.

**Authentication Setup**:
1. Generate a Figma personal access token:
   - Go to https://www.figma.com/developers/api#access-tokens
   - Click "Get personal access token"
   - Copy the token (it expires after 90 days of inactivity)

2. Set environment variable:
   ```bash
   export FIGMA_ACCESS_TOKEN="your_figma_token_here"
   ```

3. Test connectivity:
   ```bash
   # Try using the design-qa skill with a component and file
   /skill design-qa Button src/components/Button.tsx
   ```

### Troubleshooting Skills

**Problem: "MCP server not found"**
- Ensure `.mcp.json.atlassian` exists for Jira
- Verify Figma MCP is configured globally or in project
- Check MCP permissions in `.claude/settings.local.json`

**Problem: "Authentication failed"**
- Verify environment variables are set: `echo $JIRA_API_TOKEN`
- Check tokens haven't expired
- Confirm site URLs are correct (no trailing slashes)

**Problem: "Ticket/component not found"**
- Verify you have access permissions in Jira/Figma
- Check ticket ID or component name is correct
- Ensure you're using the right Jira project key

**Problem: "Connection timeout"**
- Check network connectivity
- Verify MCP SSE endpoints are accessible
- Try again with retry logic (skills will auto-retry)

### Benefits of MCP-Based Skills

These skills demonstrate:
- **Practical MCP Orchestration**: Real-world integration of external tools
- **Workflow Automation**: Reduce context-switching between tools
- **Consistency**: Standardized workflows for common tasks
- **Reusability**: Template patterns for building your own skills
- **Composability**: Skills can be combined (e.g., link Jira tickets to Figma designs)

## API Endpoints

- `POST /api/upload` - Upload CSV/JSON file
- `POST /api/query` - Process natural language query
- `GET /api/schema` - Get database schema
- `POST /api/insights` - Generate column insights
- `GET /api/health` - Health check

## Security

### MongoDB Security & NoSQL Injection Protection

The application implements comprehensive NoSQL injection protection through multiple layers:

1. **Centralized Security Module** (`core/mongo_security.py`):
   - Field name validation for collection and field names
   - Query validation to prevent malicious operators
   - Proper sanitization of user inputs
   - Dangerous operation detection and blocking ($where, eval, etc.)

2. **Input Validation**:
   - All collection and field names are validated against a whitelist pattern
   - Reserved MongoDB operators cannot be used in user-provided field names
   - File names are sanitized before creating collections
   - User queries are validated for dangerous operations

3. **Query Execution Safety**:
   - Query objects are properly structured and validated
   - Field names are sanitized to prevent operator injection
   - JavaScript execution is disabled ($where, $function, etc.)
   - Regex patterns are validated to prevent ReDoS attacks

4. **Protected Operations**:
   - File uploads with malicious names are sanitized
   - Natural language queries are validated before execution
   - Collection deletion uses validated identifiers
   - Data insights generation validates all inputs

### Security Best Practices for Development

When adding new MongoDB functionality:
1. Always use the `mongo_security` module functions
2. Never allow user input to define MongoDB operators ($, etc.)
3. Use query validation for all database operations
4. Validate all field names with security functions
5. Disable JavaScript execution in queries

### MongoDB-Specific Security Concerns

- **Operator Injection**: User input is sanitized to prevent `$where`, `$regex`, and other operator injection
- **Field Name Validation**: Ensure field names don't start with `$` or contain `.`
- **Query Structure**: All queries are validated before execution
- **Aggregation Pipeline Safety**: Pipeline stages are validated to prevent malicious operations

### Testing Security

Run the comprehensive security tests:
```bash
cd app/server
uv run pytest tests/core/test_mongo_security.py -v
```


### Additional Security Features

- CORS configured for local development only
- File upload validation (CSV and JSON only)
- Comprehensive error logging without exposing sensitive data
- Database operations are isolated with proper connection handling
- MongoDB connection uses authentication and encryption

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (requires 3.12+)
- Verify API keys are set: `echo $OPENAI_API_KEY`
- Ensure MongoDB is running: `docker ps | grep mongodb`

**MongoDB connection issues:**
- Verify MongoDB container is running: `docker-compose ps`
- Check MongoDB logs: `docker-compose logs mongodb`
- Test connection: `mongosh mongodb://localhost:27017/workshop`
- Restart MongoDB: `docker-compose restart mongodb`

**Frontend errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (requires 18+)

**CORS issues:**
- Ensure backend is running on port 8000
- Check vite.config.ts proxy settings