# Install & Prime

## Read
- README.md (Environment Configuration section)
- .env.sample (never read .env)
- ./app/server/.env.sample (never read .env)

## Read and Execute
.claude/commands/prime.md

## Run

### Environment Setup
- Run `./.claude/scripts/copy_dot_env.sh` to setup environment files
  - This script will create `app/server/.env` (required)
  - And optionally create root `.env` (for workshop features)
- The script is interactive and will guide the user through the setup

### Install Dependencies
- Install backend dependencies: `cd app/server && uv sync --all-extras`
- Install frontend dependencies: `cd app/client && npm install`

## Report
- Output the work you've just done in a concise bullet point list
- Instruct the user to edit `app/server/.env` and add their ANTHROPIC_API_KEY (required)
- If workshop features were set up, remind them to optionally edit root `.env` for MCP/hooks
- Reference the README.md "Environment Configuration" section for details about the two-file setup
