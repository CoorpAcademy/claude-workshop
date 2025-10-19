# ADW System - Deep Investigation Report

**Generated:** 2025-10-19
**Location:** `/Users/silouane/dev/tac/tac-4/adws/`

---

## Part 1: Overview

### What is ADW?

**AI Developer Workflow (ADW)** is an autonomous software development system that integrates GitHub issue management with Claude Code CLI to automatically classify, plan, implement, and deliver software changes through pull requests.

### Core Capabilities

- **Issue Classification**: Automatically categorizes GitHub issues as `/bug`, `/feature`, or `/chore`
- **Automated Planning**: Generates implementation plans using Claude AI
- **Code Implementation**: Executes plans by modifying codebase files
- **Git Operations**: Creates branches, commits, and pull requests automatically
- **Multiple Triggers**: Supports manual, cron-based, and webhook-based activation

### Quick Start

```bash
# Manual single issue processing
uv run adws/adw_plan_build.py 123

# Continuous monitoring (20s polling)
uv run adws/trigger_cron.py

# Webhook server (real-time)
uv run adws/trigger_webhook.py
```

### System Architecture

```
GitHub Issue → ADW Trigger → Classify → Plan → Implement → Commit → PR
```

---

## Part 2: Deep Investigation

### 1. System Components

#### 1.1 Core Modules

##### `agent.py` - Claude Code CLI Integration
**Location:** `adws/agent.py` (263 lines)

**Purpose:** Bridge between ADW system and Claude Code CLI

**Key Functions:**
- `check_claude_installed()` - Validates Claude CLI availability
- `prompt_claude_code(request)` - Executes Claude Code with stream-json output
- `execute_template(request)` - Runs slash commands with arguments
- `parse_jsonl_output(file)` - Parses stream-json response format
- `convert_jsonl_to_json(file)` - Creates human-readable JSON logs
- `get_claude_env()` - Configures environment variables for Claude execution
- `save_prompt(prompt, adw_id, agent_name)` - Logs prompts for debugging

**Environment Handling:**
```python
# Required environment variables
ANTHROPIC_API_KEY       # Claude AI access
CLAUDE_CODE_PATH        # CLI path (defaults to "claude")
GITHUB_PAT             # Optional: GitHub token (if different from gh auth)
E2B_API_KEY            # Optional: Sandbox environment
```

**Output Structure:**
```
agents/{adw_id}/{agent_name}/
├── raw_output.jsonl      # Stream JSON output
├── raw_output.json       # Converted array format
└── prompts/
    └── {command}.txt     # Saved prompts
```

**Critical Features:**
- Uses `--dangerously-skip-permissions` for autonomous operation
- Streams output to JSONL for real-time monitoring
- Extracts `session_id` from result messages
- Handles both success and error states

##### `data_types.py` - Type Safety Layer
**Location:** `adws/data_types.py` (144 lines)

**Purpose:** Pydantic models for type-safe data structures

**Models:**

1. **GitHub Models:**
   - `GitHubUser` - User/bot identification
   - `GitHubLabel` - Issue labels
   - `GitHubMilestone` - Project milestones
   - `GitHubComment` - Issue comments with timestamps
   - `GitHubIssue` - Full issue data with relationships
   - `GitHubIssueListItem` - Simplified list view

2. **Agent Models:**
   - `AgentPromptRequest` - Direct prompt execution
   - `AgentPromptResponse` - Execution results
   - `AgentTemplateRequest` - Slash command execution
   - `ClaudeCodeResultMessage` - Final result parsing

3. **Slash Command Types:**
```python
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature"]
SlashCommand = Literal[
    "/chore", "/bug", "/feature",
    "/classify_issue", "/find_plan_file",
    "/generate_branch_name", "/commit",
    "/pull_request", "/implement"
]
```

##### `github.py` - GitHub Operations
**Location:** `adws/github.py` (281 lines)

**Purpose:** All GitHub interactions via `gh` CLI

**Key Functions:**

- `get_repo_url()` - Extract origin URL from git remote
- `extract_repo_path(url)` - Parse owner/repo from URL
- `fetch_issue(number, repo_path)` - Get full issue details with comments
- `fetch_open_issues(repo_path)` - List all open issues (limit 1000)
- `fetch_issue_comments(repo_path, number)` - Get issue comments sorted by time
- `make_issue_comment(issue_id, comment)` - Post progress updates
- `mark_issue_in_progress(issue_id)` - Add label and assign to self
- `get_github_env()` - Configure GH_TOKEN from GITHUB_PAT

**GitHub CLI Commands Used:**
```bash
gh issue view {number} --json {fields}
gh issue list --state open --json {fields} --limit 1000
gh issue comment {number} --body {text}
gh issue edit {number} --add-label in_progress --add-assignee @me
```

##### `utils.py` - Utility Functions
**Location:** `adws/utils.py` (79 lines)

**Key Functions:**

- `make_adw_id()` - Generate 8-character UUID for workflow tracking
- `setup_logger(adw_id, trigger_type)` - Dual output (console + file) logger
- `get_logger(adw_id)` - Retrieve existing logger instance

**Logging Configuration:**
```python
# File: agents/{adw_id}/{trigger_type}/execution.log
# Format: 2025-10-19 14:32:15 - INFO - Message
# Console: INFO and above
# File: DEBUG and above
```

#### 1.2 Workflow Scripts

##### `adw_plan_build.py` - Main Workflow Orchestrator
**Location:** `adws/adw_plan_build.py` (537 lines)

**Purpose:** Complete plan-build-deliver workflow for single issue

**Agent Names:**
```python
AGENT_CLASSIFIER      = "issue_classifier"
AGENT_PLANNER        = "sdlc_planner"
AGENT_IMPLEMENTOR    = "sdlc_implementor"
AGENT_PLAN_FINDER    = "plan_finder"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR     = "pr_creator"
```

**Workflow Execution:**

```
1. Parse Args & Setup Logger
   ├─ Issue number (required)
   ├─ ADW ID (optional, generates if missing)
   └─ Initialize logger: agents/{adw_id}/adw_plan_build/execution.log

2. Environment Validation
   ├─ Check ANTHROPIC_API_KEY
   └─ Check CLAUDE_CODE_PATH

3. Repository Setup
   ├─ Get git remote URL
   └─ Extract owner/repo path

4. Fetch Issue
   ├─ Use gh CLI to get issue details
   └─ Post comment: "{adw_id}_ops: ✅ Starting ADW workflow"

5. Classify Issue
   ├─ Agent: issue_classifier
   ├─ Command: /classify_issue {issue_json}
   ├─ Model: sonnet
   ├─ Output: /chore, /bug, /feature, or 0
   └─ Post comment: "{adw_id}_ops: ✅ Issue classified as: {command}"

6. Create Git Branch
   ├─ Agent: branch_generator
   ├─ Command: /generate_branch_name {type} {adw_id} {issue_json}
   ├─ Model: sonnet
   ├─ Actions: git checkout main, git pull, git checkout -b {branch}
   ├─ Format: {type}-{number}-{adw_id}-{slug}
   └─ Post comment: "{adw_id}_ops: ✅ Working on branch: {branch}"

7. Build Implementation Plan
   ├─ Agent: sdlc_planner
   ├─ Command: /{type} {title}: {body}
   ├─ Model: sonnet
   ├─ Output: Creates plan file in specs/ directory
   └─ Post comment: "{adw_id}_sdlc_planner: ✅ Implementation plan created"

8. Find Plan File
   ├─ Agent: plan_finder
   ├─ Command: /find_plan_file {plan_output}
   ├─ Model: sonnet
   ├─ Output: Path to plan file (e.g., specs/add-feature-plan.md)
   └─ Post comment: "{adw_id}_ops: ✅ Plan file created: {path}"

9. Commit Plan
   ├─ Agent: sdlc_planner_committer
   ├─ Command: /commit {agent} {type} {issue_json}
   ├─ Model: sonnet
   ├─ Actions: git add, git commit
   └─ Post comment: "{adw_id}_sdlc_planner: ✅ Committing plan"

10. Implement Solution
    ├─ Agent: sdlc_implementor
    ├─ Command: /implement {plan_file}
    ├─ Model: sonnet
    ├─ Actions: Read plan, modify files, run tests
    └─ Post comment: "{adw_id}_sdlc_implementor: ✅ Solution implemented"

11. Commit Implementation
    ├─ Agent: sdlc_implementor_committer
    ├─ Command: /commit {agent} {type} {issue_json}
    ├─ Model: sonnet
    ├─ Actions: git add, git commit
    └─ Post comment: "{adw_id}_sdlc_implementor: ✅ Committing implementation"

12. Create Pull Request
    ├─ Agent: pr_creator
    ├─ Command: /pull_request {branch} {issue_json} {plan_file} {adw_id}
    ├─ Model: sonnet
    ├─ Actions: git push, gh pr create
    ├─ Output: PR URL
    └─ Post comment: "{adw_id}_ops: ✅ Pull request created: {url}"

13. Success
    └─ Post comment: "{adw_id}_ops: ✅ ADW workflow completed successfully"
```

**Error Handling:**
```python
# Centralized error checking via check_error()
# On error:
#   1. Log error message
#   2. Post failure comment to issue
#   3. Exit with code 1
```

**Comment Format:**
```
{adw_id}_{agent_name}_{session_id}: {message}
# Examples:
a1b2c3d4_ops: ✅ Starting ADW workflow
a1b2c3d4_sdlc_planner_session123: ✅ Implementation plan created
```

##### `trigger_cron.py` - Polling Monitor
**Location:** `adws/trigger_cron.py` (224 lines)

**Purpose:** Continuous monitoring with scheduled polling

**Polling Logic:**
```python
INTERVAL = 20  # seconds

# Process issue if:
# 1. Issue has NO comments (new issue)
# 2. Latest comment body is exactly "adw" (trigger word)
```

**State Tracking:**
```python
processed_issues: Set[int]              # Issues processed in session
issue_last_comment: Dict[int, str]      # Last processed comment ID per issue
```

**Workflow:**
```
Every 20 seconds:
1. Fetch all open issues (limit 1000)
2. For each issue:
   ├─ Skip if already processed in session
   ├─ Fetch comments
   ├─ Check if qualifies (no comments OR latest = "adw")
   └─ If qualified: Launch adw_plan_build.py
3. Track processed issues
4. Log performance metrics
```

**Process Spawning:**
```python
cmd = [sys.executable, "adw_plan_build.py", str(issue_number)]
result = subprocess.run(cmd, capture_output=True, text=True)
```

**Graceful Shutdown:**
```python
# Handles SIGINT (Ctrl+C) and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

**Deployment:**
```bash
# Systemd service for production
sudo systemctl enable adw-cron
sudo systemctl start adw-cron
```

##### `trigger_webhook.py` - Real-time Webhook Server
**Location:** `adws/trigger_webhook.py` (207 lines)

**Purpose:** FastAPI server for instant GitHub event processing

**Server Configuration:**
```python
PORT = int(os.getenv("PORT", "8001"))
HOST = "0.0.0.0"
```

**Endpoints:**

1. **POST /gh-webhook** - GitHub Event Handler
   ```python
   # Triggers on:
   # 1. Event: "issues", Action: "opened"
   # 2. Event: "issue_comment", Action: "created", Body: "adw"

   # Response within GitHub's 10-second timeout
   # Background process spawned via subprocess.Popen
   ```

2. **GET /health** - Health Check
   ```python
   # Runs adws/health_check.py
   # Returns system status, warnings, errors
   ```

**Event Processing:**
```python
# Parse webhook payload
event_type = headers["X-GitHub-Event"]
action = payload["action"]
issue_number = payload["issue"]["number"]
comment_body = payload["comment"]["body"].strip().lower()

# Spawn background process
cmd = ["uv", "run", "adw_plan_build.py", str(issue_number), adw_id]
process = subprocess.Popen(cmd, cwd=project_root, env=os.environ.copy())

# Return immediately (< 10s)
return {
    "status": "accepted",
    "adw_id": adw_id,
    "logs": f"agents/{adw_id}/adw_plan_build/"
}
```

**GitHub Webhook Setup:**
```
URL: https://your-domain.com/gh-webhook
Events: Issues, Issue comments
Content type: application/json
```

**Tunnel Exposure:**
```bash
# For local development
cloudflared tunnel --url http://localhost:8001
# Or use scripts/expose_webhook.sh
```

##### `health_check.py` - System Diagnostics
**Location:** `adws/health_check.py` (397 lines)

**Purpose:** Comprehensive system validation

**Checks Performed:**

1. **Environment Variables** (`check_env_vars`)
   ```python
   # Required:
   ANTHROPIC_API_KEY  # Must be set
   CLAUDE_CODE_PATH   # Defaults to "claude"

   # Optional:
   GITHUB_PAT              # GitHub token
   E2B_API_KEY            # Sandbox API
   CLOUDFLARED_TUNNEL_TOKEN  # Webhook tunnel
   ```

2. **Git Repository** (`check_git_repo`)
   ```python
   # Validates:
   - Git remote origin exists
   - Can extract owner/repo path
   - Warns if still using "disler" repo (template origin)
   ```

3. **GitHub CLI** (`check_github_cli`)
   ```python
   # Tests:
   - gh --version (installed)
   - gh auth status (authenticated)
   ```

4. **Claude Code CLI** (`check_claude_code`)
   ```python
   # Tests:
   - claude --version (installed)
   - Runs test prompt: "What is 2+2?"
   - Verifies response contains "4"
   - Uses model: claude-3-5-haiku-20241022
   - Timeout: 30 seconds
   ```

**Output:**
```bash
🏥 Running ADW System Health Check...

✅ Overall Status: HEALTHY
📅 Timestamp: 2025-10-19T14:32:15

📋 Check Results:
--------------------------------------------------

✅ Environment:
   claude_code_path: claude

✅ Git Repository:
   repo_url: https://github.com/owner/repo
   repo_path: owner/repo

✅ GitHub CLI:
   installed: True
   authenticated: True

✅ Claude Code:
   test_passed: True
   response: 4

⚠️  Warnings:
   - Repository still points to 'disler'

📝 Next Steps:
   1. Fork repository to your own account
```

**Usage:**
```bash
# Standalone
uv run adws/health_check.py

# Post results to issue
uv run adws/health_check.py 123
```

### 2. Claude Code Slash Commands

#### Location: `.claude/commands/`

##### `/classify_issue` - Issue Categorization
**File:** `.claude/commands/classify_issue.md`

**Input:** GitHub issue JSON
**Output:** `/chore`, `/bug`, `/feature`, or `0`

**Logic:**
```markdown
Based on issue content:
- /chore  → Maintenance, docs, refactoring
- /bug    → Bug fixes, corrections
- /feature → New features, enhancements
- 0       → Unclassifiable
```

##### `/generate_branch_name` - Branch Creation
**File:** `.claude/commands/generate_branch_name.md`

**Inputs:**
- `$1` - issue_class (chore/bug/feature)
- `$2` - adw_id (8-char UUID)
- `$3` - issue JSON

**Format:** `<class>-<number>-<adw_id>-<slug>`

**Examples:**
```
feat-123-a1b2c3d4-add-user-auth
bug-456-e5f6g7h8-fix-login-error
chore-789-i9j0k1l2-update-dependencies
```

**Actions:**
```bash
git checkout main
git pull
git checkout -b {branch_name}
```

##### `/implement` - Plan Execution
**File:** `.claude/commands/implement.md`

**Input:** Path to plan file
**Actions:**
1. Read plan from specs/ directory
2. Implement changes to codebase
3. Run tests if applicable
4. Report work completed

**Output:**
```markdown
Summary:
- Implemented feature X
- Modified files: file1.py, file2.ts
- Added tests

git diff --stat:
file1.py | 45 ++++++++++++++++++++++++++++++++++
file2.ts | 23 +++++++++++++++--
2 files changed, 66 insertions(+), 2 deletions(-)
```

### 3. Data Flow & Architecture

#### 3.1 ADW ID Tracking System

**Generation:**
```python
adw_id = str(uuid.uuid4())[:8]  # e.g., "a1b2c3d4"
```

**Propagation:**
```
CLI Args → All Agents → Issue Comments → Git Commits → PR Description
```

**Directory Structure:**
```
agents/
└── a1b2c3d4/                    # ADW ID
    ├── adw_plan_build/
    │   └── execution.log        # Main workflow log
    ├── issue_classifier/
    │   ├── raw_output.jsonl
    │   ├── raw_output.json
    │   └── prompts/
    │       └── classify_issue.txt
    ├── sdlc_planner/
    │   ├── raw_output.jsonl
    │   ├── raw_output.json
    │   └── prompts/
    │       ├── chore.txt
    │       ├── bug.txt
    │       └── feature.txt
    ├── plan_finder/
    │   └── ...
    ├── branch_generator/
    │   └── ...
    ├── sdlc_planner_committer/
    │   └── ...
    ├── sdlc_implementor/
    │   └── ...
    ├── sdlc_implementor_committer/
    │   └── ...
    └── pr_creator/
        └── ...
```

#### 3.2 Communication Flow

```
GitHub Issue
    ↓
Trigger (Manual/Cron/Webhook)
    ↓
adw_plan_build.py
    ↓
    ├─→ agent.execute_template()
    │       ↓
    │   Claude Code CLI
    │       ↓
    │   JSONL Output
    │       ↓
    │   Parse Result
    │       ↓
    │   Return to Workflow
    │
    ├─→ github.make_issue_comment()
    │       ↓
    │   gh issue comment
    │       ↓
    │   GitHub API
    │
    └─→ logger.info()
            ↓
        Console + File
```

#### 3.3 Model Selection

**Default Configuration:**
```python
# adw_plan_build.py
model="sonnet"  # All agents use Sonnet by default

# Available models
"sonnet"  # Claude 3.5 Sonnet - Fast, cost-effective
"opus"    # Claude 3 Opus - More capable, slower, expensive
```

**Cost Optimization:**
- Classification: Sonnet (simple decision)
- Planning: Sonnet (structured output)
- Implementation: Sonnet (code generation)
- All workflows: Sonnet by default

### 4. Requirements & Dependencies

#### 4.1 System Requirements

**Operating System:**
- macOS, Linux, Windows (WSL recommended)

**Runtime:**
- Python 3.12+
- Node.js 18+ (not required for ADW, but for main app)

**CLI Tools:**
- `gh` - GitHub CLI
- `git` - Version control
- `uv` - Python package manager
- `claude` - Claude Code CLI

#### 4.2 Python Dependencies

**From `adw_plan_build.py`:**
```python
python-dotenv  # Environment variable loading
pydantic      # Type-safe data models
```

**From `trigger_cron.py`:**
```python
schedule      # Cron job scheduling
python-dotenv
pydantic
```

**From `trigger_webhook.py`:**
```python
fastapi       # Web framework
uvicorn       # ASGI server
python-dotenv
```

**From `health_check.py`:**
```python
python-dotenv
pydantic
```

**Installation:**
```bash
# All dependencies managed via uv run
# No manual installation needed
uv run adws/adw_plan_build.py 123
```

#### 4.3 Environment Variables

**Required:**
```bash
ANTHROPIC_API_KEY="sk-ant-..."
```

**Optional:**
```bash
CLAUDE_CODE_PATH="/usr/local/bin/claude"  # Default: "claude"
GITHUB_PAT="ghp_..."                      # Only if not using gh auth
E2B_API_KEY="..."                         # For sandbox environments
CLOUDFLARED_TUNNEL_TOKEN="..."            # For webhook tunneling
PORT="8001"                               # Webhook server port
```

**Setup:**
```bash
# Root directory
cp .env.sample .env
# Edit .env with your API keys

# Server directory (if using main app)
cp app/server/.env.sample app/server/.env
```

#### 4.4 GitHub Configuration

**Authentication:**
```bash
# Method 1: gh CLI (recommended)
gh auth login

# Method 2: GITHUB_PAT environment variable
export GITHUB_PAT="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Repository Setup:**
```bash
# Must be in a git repository with remote
git remote -v
# origin  https://github.com/owner/repo (fetch)
# origin  https://github.com/owner/repo (push)
```

**Webhook Configuration (for trigger_webhook.py):**
```
GitHub Settings → Webhooks → Add webhook
Payload URL: https://your-domain.com/gh-webhook
Content type: application/json
Events: Issues, Issue comments
```

### 5. Usage Patterns

#### 5.1 Manual Processing

**Single Issue:**
```bash
# Process specific issue
uv run adws/adw_plan_build.py 123

# With custom ADW ID
uv run adws/adw_plan_build.py 123 custom01
```

**Output Locations:**
```
agents/a1b2c3d4/adw_plan_build/execution.log  # Main log
agents/a1b2c3d4/*/raw_output.jsonl          # Agent outputs
specs/issue-123-plan.md                      # Implementation plan
```

**GitHub Comments:**
```
a1b2c3d4_ops: ✅ Starting ADW workflow
a1b2c3d4_ops: ✅ Issue classified as: /feature
a1b2c3d4_ops: ✅ Working on branch: feat-123-a1b2c3d4-add-auth
a1b2c3d4_sdlc_planner: ✅ Implementation plan created
a1b2c3d4_ops: ✅ Plan file created: specs/add-auth-plan.md
a1b2c3d4_sdlc_implementor: ✅ Solution implemented
a1b2c3d4_ops: ✅ Pull request created: https://github.com/...
a1b2c3d4_ops: ✅ ADW workflow completed successfully
```

#### 5.2 Cron Monitoring

**Start Monitor:**
```bash
uv run adws/trigger_cron.py
# INFO: Starting ADW cron trigger
# INFO: Repository: owner/repo
# INFO: Polling interval: 20 seconds
```

**Trigger Conditions:**
1. **New Issue:** Any issue with 0 comments
2. **Manual Trigger:** Comment "adw" on any issue

**Logs:**
```
INFO: Starting issue check cycle
INFO: Fetched 5 open issues
INFO: Issue #123 has no comments - marking for processing
INFO: Found 1 new qualifying issues: [123]
INFO: Triggering ADW workflow for issue #123
INFO: Successfully triggered workflow for issue #123
INFO: Check cycle completed in 2.34 seconds
INFO: Total processed issues in session: 1
```

**State Management:**
```python
# In-memory tracking (resets on restart)
processed_issues = {123, 456, 789}
issue_last_comment = {123: "comment_id_xyz"}
```

**Production Deployment:**
```bash
# systemd service file
[Unit]
Description=ADW Cron Trigger
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/tac-4
ExecStart=/path/to/uv run adws/trigger_cron.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 5.3 Webhook Server

**Start Server:**
```bash
uv run adws/trigger_webhook.py
# Starting ADW Webhook Trigger on port 8001
# Starting server on http://0.0.0.0:8001
# Webhook endpoint: POST /gh-webhook
# Health check: GET /health
```

**Tunnel Setup (Local Development):**
```bash
# Using cloudflared
cloudflared tunnel --url http://localhost:8001

# Using ngrok
ngrok http 8001

# Using provided script
./scripts/expose_webhook.sh
```

**GitHub Webhook Events:**
```json
// Issue Opened
{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "Add authentication",
    "body": "We need user login..."
  }
}

// Comment "adw"
{
  "action": "created",
  "issue": {"number": 123},
  "comment": {
    "body": "adw",
    "user": {"login": "developer"}
  }
}
```

**Server Response:**
```json
{
  "status": "accepted",
  "issue": 123,
  "adw_id": "a1b2c3d4",
  "message": "ADW workflow triggered for issue #123",
  "reason": "New issue opened",
  "logs": "agents/a1b2c3d4/adw_plan_build/"
}
```

**Health Check:**
```bash
curl http://localhost:8001/health
```

```json
{
  "status": "healthy",
  "service": "adw-webhook-trigger",
  "health_check": {
    "success": true,
    "warnings": [],
    "errors": [],
    "details": "Run health_check.py directly for full report"
  }
}
```

### 6. Advanced Features

#### 6.1 Session ID Tracking

**Purpose:** Track individual Claude Code sessions

**Extraction:**
```python
# From JSONL result message
{
  "type": "result",
  "session_id": "session_abc123xyz",
  "is_error": false,
  "result": "Implementation complete",
  "total_cost_usd": 0.0045,
  "duration_ms": 12500
}
```

**Usage in Comments:**
```
{adw_id}_{agent_name}_{session_id}: {message}
a1b2c3d4_sdlc_planner_session_abc123: ✅ Plan created
```

#### 6.2 Cost Tracking

**Available in JSONL Output:**
```python
class ClaudeCodeResultMessage:
    total_cost_usd: float      # Total API cost
    duration_ms: int           # Total execution time
    duration_api_ms: int       # API call time
    num_turns: int            # Conversation turns
```

**Typical Costs (Sonnet):**
- Classification: ~$0.001
- Planning: ~$0.01-0.05
- Implementation: ~$0.05-0.20
- Total per issue: ~$0.06-0.26

#### 6.3 Error Recovery

**Centralized Error Handler:**
```python
def check_error(error_or_response, issue_number, adw_id,
                agent_name, error_prefix, logger):
    """
    - Logs error to console + file
    - Posts failure comment to GitHub
    - Exits with code 1
    """
```

**Failure Points:**
1. **Environment Check** → Missing API keys
2. **Git Operations** → No remote, merge conflicts
3. **Issue Classification** → Returns "0"
4. **Plan Generation** → Claude execution fails
5. **Implementation** → Tests fail, syntax errors
6. **Git Commit** → Merge conflicts, pre-commit hooks
7. **PR Creation** → Branch already exists, no changes

**Recovery Actions:**
```bash
# Check logs
cat agents/{adw_id}/adw_plan_build/execution.log

# Check agent output
cat agents/{adw_id}/{agent_name}/raw_output.json | jq .

# Manual retry
uv run adws/adw_plan_build.py {issue_number} {adw_id}
```

#### 6.4 Git Integration

**Branch Naming Convention:**
```
{type}-{number}-{adw_id}-{slug}

Examples:
feat-123-a1b2c3d4-user-authentication
bug-456-e5f6g7h8-fix-login-timeout
chore-789-i9j0k1l2-update-readme
```

**Commit Message Format:**
```
{type}: {description} for #{issue_number}

Generated with ADW ID: {adw_id}
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**PR Creation:**
```markdown
## Summary
- Implemented user authentication system
- Added JWT token validation
- Created login/logout endpoints

## Test Plan
- [ ] Test login with valid credentials
- [ ] Test logout functionality
- [ ] Verify JWT token expiration

🤖 Generated with [Claude Code](https://claude.ai/code)
```

### 7. Security Considerations

#### 7.1 Permissions

**Dangerous Flag:**
```python
dangerously_skip_permissions=True
# Bypasses Claude Code permission prompts
# Required for autonomous operation
# Use only in trusted environments
```

**Git Safety:**
```python
# Claude Code follows these rules:
# - NEVER push --force to main/master
# - NEVER run hard reset
# - NEVER skip hooks without explicit request
# - ALWAYS check authorship before amend
```

#### 7.2 API Key Management

**Best Practices:**
```bash
# Store in .env (gitignored)
ANTHROPIC_API_KEY="sk-ant-..."

# Never hardcode in scripts
# Never commit to repository
# Use minimal scopes for GITHUB_PAT
```

**GitHub Token Scopes:**
```
repo          # Full control of repositories
workflow      # Update GitHub Actions workflows
write:packages # Upload packages
```

#### 7.3 Webhook Security

**Recommendations:**
```python
# 1. Use HTTPS only
# 2. Validate webhook signatures (not implemented)
# 3. Rate limiting (not implemented)
# 4. IP whitelisting via firewall
# 5. Monitor for abuse
```

### 8. Limitations & Constraints

#### 8.1 Known Limitations

1. **No Webhook Signature Validation**
   - Accepts any POST to /gh-webhook
   - Vulnerable to spoofing

2. **No Rate Limiting**
   - Unlimited concurrent workflows possible
   - Could exhaust API quotas

3. **Single Repository**
   - Works with one repo at a time
   - No multi-repo orchestration

4. **No Retry Logic**
   - Failed workflows must be manually restarted
   - No exponential backoff

5. **State is In-Memory**
   - Cron trigger loses state on restart
   - No persistence between runs

6. **No Conflict Resolution**
   - Assumes clean merges
   - Manual intervention needed for conflicts

#### 8.2 API Rate Limits

**GitHub:**
```
Authenticated: 5000 requests/hour
Issue views: ~1 request per call
Issue comments: ~1 request per call

Workflow consumption:
- Manual: ~5-10 requests
- Cron (20s): ~180 issue fetches/hour
```

**Anthropic:**
```
Tier 1: 50 requests/minute
Tier 2: 1000 requests/minute

Workflow consumption:
- Classification: 1 request
- Planning: 1-3 requests
- Implementation: 3-10 requests
- Total: ~5-14 requests per issue
```

#### 8.3 Claude Code Limitations

**Timeout:**
```python
# Default: No timeout in agent.py
# Recommendation: Set timeout for production

result = subprocess.run(
    cmd,
    stdout=f,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
    timeout=300  # 5 minutes
)
```

**Context Window:**
```
Sonnet: 200K tokens input
- Large codebases may exceed limits
- Plan files should be concise
```

### 9. Extension Points

#### 9.1 Custom Slash Commands

**Add New Command:**
```bash
# 1. Create command file
.claude/commands/my_command.md

# 2. Update data_types.py
SlashCommand = Literal[
    ...,
    "/my_command"
]

# 3. Add to workflow
request = AgentTemplateRequest(
    agent_name="my_agent",
    slash_command="/my_command",
    args=["arg1", "arg2"],
    adw_id=adw_id
)
```

#### 9.2 Additional Triggers

**Example: Slack Integration**
```python
# slack_trigger.py
from slack_sdk import WebClient

@app.event("message")
def handle_message(event):
    if event["text"] == "adw issue 123":
        trigger_workflow(123)
```

**Example: Email Parsing**
```python
# email_trigger.py
import imaplib

def check_inbox():
    # Parse emails for issue numbers
    # Trigger workflows
```

#### 9.3 Custom Agents

**Add Specialized Agent:**
```python
# In adw_plan_build.py
AGENT_CODE_REVIEWER = "code_reviewer"

def review_code(adw_id, logger):
    request = AgentTemplateRequest(
        agent_name=AGENT_CODE_REVIEWER,
        slash_command="/review_code",
        args=[],
        adw_id=adw_id
    )
    return execute_template(request)
```

### 10. Troubleshooting Guide

#### 10.1 Common Issues

**Issue: "Claude Code CLI is not installed"**
```bash
# Solution 1: Install Claude Code
# Visit: https://docs.anthropic.com/en/docs/claude-code

# Solution 2: Set path
export CLAUDE_CODE_PATH="/path/to/claude"
```

**Issue: "GitHub CLI (gh) is not installed"**
```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Authenticate
gh auth login
```

**Issue: "Missing ANTHROPIC_API_KEY"**
```bash
# Get API key from https://console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .env
echo 'ANTHROPIC_API_KEY="sk-ant-..."' >> .env
```

**Issue: "No git remote 'origin' found"**
```bash
# Check remotes
git remote -v

# Add remote
git remote add origin https://github.com/owner/repo.git
```

**Issue: Workflow hangs**
```bash
# Check agent output
tail -f agents/{adw_id}/{agent_name}/raw_output.jsonl

# Check execution log
tail -f agents/{adw_id}/adw_plan_build/execution.log

# Kill if needed
pkill -f adw_plan_build
```

#### 10.2 Debug Mode

**Enable Verbose Logging:**
```python
# In utils.py, change:
console_handler.setLevel(logging.DEBUG)

# Or add environment variable
export ADW_DEBUG=true
```

**Inspect Agent Output:**
```bash
# View JSONL stream
cat agents/{adw_id}/{agent_name}/raw_output.jsonl

# Pretty print JSON
cat agents/{adw_id}/{agent_name}/raw_output.json | jq .

# Check specific message
cat agents/{adw_id}/{agent_name}/raw_output.jsonl | \
  jq 'select(.type == "result")'
```

#### 10.3 Health Check

**Run Diagnostics:**
```bash
uv run adws/health_check.py

# Expected output:
✅ Overall Status: HEALTHY
📋 Check Results:
--------------------------------------------------
✅ Environment
✅ Git Repository
✅ GitHub CLI
✅ Claude Code
```

### 11. Performance Metrics

#### 11.1 Typical Execution Times

**Single Issue Workflow:**
```
Classification:     5-10s
Planning:          30-60s
Plan Commit:        5-10s
Implementation:    60-180s
Implementation Commit: 5-10s
PR Creation:       10-20s
---------------------------
Total:            115-290s (~2-5 minutes)
```

**Cron Monitoring:**
```
Issue Fetch (100 issues): 2-5s
Check Cycle:             2-10s
Cycles per hour:         180
```

#### 11.2 Resource Usage

**Memory:**
```
adw_plan_build.py:  ~50-100 MB
trigger_cron.py:    ~30-50 MB
trigger_webhook.py: ~40-60 MB
```

**Disk:**
```
Per workflow:
- Logs: ~100-500 KB
- JSONL outputs: ~50-200 KB per agent
- Total: ~500 KB - 2 MB per issue
```

**Network:**
```
GitHub API: ~1-2 MB per workflow
Anthropic API: ~5-20 MB per workflow
```

### 12. Best Practices

#### 12.1 Repository Setup

1. **Fork Template Repository**
   ```bash
   # Don't use disler's repo directly
   gh repo fork disler/original --clone
   ```

2. **Branch Protection**
   ```
   GitHub Settings → Branches → Add rule
   - Require pull request reviews
   - Require status checks
   - Restrict pushes to main
   ```

3. **Issue Templates**
   ```markdown
   .github/ISSUE_TEMPLATE/feature.md
   .github/ISSUE_TEMPLATE/bug.md
   ```

#### 12.2 Workflow Optimization

1. **Use Webhook for Real-time**
   ```bash
   # Fastest response time
   uv run adws/trigger_webhook.py
   ```

2. **Batch Processing**
   ```bash
   # Process multiple issues
   for issue in 123 124 125; do
       uv run adws/adw_plan_build.py $issue &
   done
   wait
   ```

3. **Model Selection**
   ```python
   # Quick tasks: sonnet (default)
   # Complex tasks: opus
   model = "opus" if complexity > threshold else "sonnet"
   ```

#### 12.3 Monitoring

1. **Log Aggregation**
   ```bash
   # Centralize logs
   tail -f agents/*/adw_plan_build/execution.log
   ```

2. **Cost Tracking**
   ```bash
   # Extract costs from JSONL
   grep -r "total_cost_usd" agents/ | \
     jq -s 'add' | \
     jq '{total: (map(.total_cost_usd) | add)}'
   ```

3. **Success Rate**
   ```bash
   # Count successful workflows
   grep -r "✅ ADW workflow completed successfully" agents/
   ```

---

## Appendix

### A. File Inventory

```
adws/
├── README.md              (267 lines) - User documentation
├── adw_plan_build.py      (537 lines) - Main workflow orchestrator
├── agent.py               (263 lines) - Claude Code CLI integration
├── data_types.py          (144 lines) - Pydantic models
├── github.py              (281 lines) - GitHub API operations
├── health_check.py        (397 lines) - System diagnostics
├── trigger_cron.py        (224 lines) - Polling monitor
├── trigger_webhook.py     (207 lines) - Webhook server
└── utils.py                (79 lines) - Utility functions

Total: ~2,399 lines of Python code
```

### B. Environment Template

```bash
# .env template for ADW system

# Required
ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Optional
CLAUDE_CODE_PATH="claude"
GITHUB_PAT="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
E2B_API_KEY="your-e2b-api-key"
CLOUDFLARED_TUNNEL_TOKEN="your-tunnel-token"
PORT="8001"
```

### C. Quick Reference Commands

```bash
# Manual processing
uv run adws/adw_plan_build.py {issue_number}

# Cron monitoring
uv run adws/trigger_cron.py

# Webhook server
uv run adws/trigger_webhook.py

# Health check
uv run adws/health_check.py

# View logs
cat agents/{adw_id}/adw_plan_build/execution.log

# View agent output
cat agents/{adw_id}/{agent_name}/raw_output.json | jq .

# Trigger via comment
# Comment "adw" on any GitHub issue
```

### D. ADW ID Examples

```
a1b2c3d4  # Manual trigger
e5f6g7h8  # Cron trigger
i9j0k1l2  # Webhook trigger
m3n4o5p6  # Custom ID provided
```

---

**Report End**

*For latest documentation, see: `adws/README.md`*
*For system health: `uv run adws/health_check.py`*
