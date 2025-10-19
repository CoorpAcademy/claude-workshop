# Natural Language MongoDB Query Interface

A web application that converts natural language queries to MongoDB queries using AI, built with FastAPI and Vite + TypeScript.

## Features

- 🗣️ Natural language to MongoDB query conversion using OpenAI or Anthropic
- 📁 Drag-and-drop file upload (.csv and .json)
- 📊 Interactive table results display
- ⚡ Fast development with Vite and uv

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose (for MongoDB)
- OpenAI API key and/or Anthropic API key
- 'gh' github cli
- astral uv

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

### 2. Install Dependencies

```bash
# Backend
cd app/server
uv sync --all-extras

# Frontend
cd app/client
npm install
```

### 3. Environment Configuration

Set up your API keys and MongoDB connection in the server directory:

```bash
cp .env.sample .env
```

and

```bash
cd app/server
cp .env.sample .env
# Edit .env and add your API keys and MongoDB connection string
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
├── adws/                   # AI Developer Workflows - Core agent system
├── scripts/                # Utility scripts (start.sh, stop_apps.sh)
├── specs/                  # Feature specifications
├── ai_docs/                # AI/LLM documentation
├── agents/                 # Agent execution logging
└── logs/                   # Structured session logs
```

## ADWs

- `uv run adws/health_check.py` - Basic health check ADW
- `uv run adws/trigger_webhook.py` - React to incoming webhook trigger (be sure to setup a tunnel and your github webhook)
- `uv run adws/trigger_cron.py` - Simple cron job trigger that checks github issues every N seconds
- `uv run adws/adw_plan_build.py` - Plan -> Build AI Developer Workflow (ADW)

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