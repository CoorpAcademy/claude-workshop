# Chore: Create Initialization Script for Non-Technical Users

## Chore Description
Create an `init.sh` script that automates the complete setup process for non-technical users who only have GitHub and VSCode installed. The script should check for required dependencies (Docker, Node.js, Python/uv), install them if missing, clone the repository if needed, set up environment variables, install all dependencies, and start the application. The goal is to provide a one-command setup experience that guides users through the entire process with clear, friendly messages.

## Relevant Files
Use these files to resolve the chore:

- `README.md` - Contains prerequisites and setup instructions that need to be automated
- `scripts/start_mongodb.sh` - MongoDB startup logic to integrate
- `scripts/start.sh` - Application startup logic to integrate
- `docker-compose.yml` - MongoDB and Mongo Express configuration
- `.env.sample` - Root environment sample file
- `app/server/.env.sample` - Server environment sample file with API keys configuration
- `app/server/pyproject.toml` - Python dependencies configuration
- `app/client/package.json` - Frontend dependencies configuration

### New Files
- `init.sh` - Main initialization script for non-technical users (to be created at project root)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create the init.sh script structure
- Create `init.sh` in the project root with executable permissions
- Add shebang and set up error handling with `set -e`
- Define color codes for user-friendly output (GREEN, YELLOW, RED, BLUE, NC)
- Create helper functions: `print_success`, `print_error`, `print_warning`, `print_info`, `print_step`
- Add function to detect OS (macOS vs Linux) for appropriate package manager commands

### 2. Implement dependency checking functions
- Create `check_command()` function to verify if a command exists
- Create `check_docker()` function to verify Docker installation and running status
- Create `check_node()` function to verify Node.js 18+ is installed
- Create `check_python()` function to verify Python 3.10+ is installed
- Create `check_uv()` function to verify astral uv is installed
- Create `check_gh()` function to verify GitHub CLI is installed and authenticated
- Create `check_git()` function to verify git is installed

### 3. Implement dependency installation functions
- Create `install_docker()` function with OS-specific instructions (macOS: Homebrew, Linux: apt/yum)
- Create `install_node()` function using nvm or package manager
- Create `install_python()` function with version check (recommend pyenv or system package manager)
- Create `install_uv()` function using official installer: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Create `install_gh()` function using package manager or official installer
- Create `install_git()` function using package manager
- Each install function should prompt user for confirmation before installation

### 4. Implement environment setup functions
- Create `setup_env_files()` function to copy .env.sample files to .env
- Prompt user for API keys (OpenAI and/or Anthropic) with clear instructions
- Create function to validate API key format (basic check for non-empty and reasonable length)
- Update `app/server/.env` with MongoDB connection string and user-provided API keys
- Update root `.env` if ADW features will be used (optional)
- Provide option to skip API key setup and configure later

### 5. Implement repository setup
- Check if script is running from within the repository or needs to clone
- If not in repo, prompt for clone location (default: `~/workshow-claude`)
- Clone repository using `gh repo clone` or `git clone` if not already present
- Navigate to repository directory
- Verify all expected files and directories exist

### 6. Implement dependency installation orchestration
- Create `install_backend_deps()` function running: `cd app/server && uv sync --all-extras`
- Create `install_frontend_deps()` function running: `cd app/client && npm install`
- Handle errors gracefully with clear messages
- Show progress indicators during installation

### 7. Implement MongoDB setup
- Create `setup_mongodb()` function to check if Docker is running
- Start Docker if not running (or prompt user to start it manually)
- Run MongoDB setup using `./scripts/start_mongodb.sh`
- Verify MongoDB is healthy and accessible
- Show Mongo Express GUI URL (http://localhost:8081)

### 8. Create main initialization flow
- Welcome message explaining what the script will do
- Run all dependency checks sequentially
- For each missing dependency, prompt user to install it
- After all dependencies are met, proceed with project setup
- Set up environment files with user input
- Install backend and frontend dependencies
- Set up and start MongoDB
- Offer to start the application immediately or provide manual start instructions

### 9. Implement post-installation instructions
- Create summary of what was installed and configured
- Show how to start the application: `./scripts/start.sh`
- Show how to access the application: Frontend (http://localhost:5173), Backend (http://localhost:8000)
- Show how to access MongoDB GUI: Mongo Express (http://localhost:8081)
- Provide troubleshooting tips: check `README.md`, verify MongoDB is running, check API keys
- Create a simple verification test: curl health endpoint or open browser

### 10. Add safety and recovery features
- Create cleanup function to handle script interruption (Ctrl+C)
- Create log file for debugging: `init.log`
- Add option to resume installation if partially completed
- Add option to reset/clean installation and start fresh
- Detect if running on unsupported OS and provide guidance

### 11. Test the initialization script
- Test on fresh system (or VM) with only VSCode and GitHub
- Test with all dependencies already installed (should skip installation)
- Test with partial dependencies (e.g., Docker installed, Node.js missing)
- Test API key validation and .env file creation
- Test error handling for invalid inputs
- Test interruption and resume scenarios

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `chmod +x init.sh` - Make initialization script executable
- `shellcheck init.sh` - Lint the shell script for common errors (install shellcheck if needed)
- `./init.sh --help` - Verify help message displays correctly
- `./init.sh --check` - Run dependency check mode without installing anything
- Review init.log for any errors during test run
- Verify MongoDB starts successfully: `docker ps | grep nlq_mongodb`
- Verify backend dependencies installed: `cd app/server && uv run pytest`
- Verify frontend dependencies installed: `cd app/client && npm run build`
- Start application and verify all endpoints work: `./scripts/start.sh`

## Notes
- The script should be idempotent: running it multiple times should not cause issues
- Use interactive prompts with sensible defaults to guide non-technical users
- Provide clear error messages with actionable solutions
- Consider creating a `--unattended` mode for CI/CD environments
- The script should validate that GitHub CLI is authenticated before attempting to use it
- Include a `--dry-run` option to show what would be done without making changes
- macOS users may need to install Homebrew first - provide instructions
- Windows users should use WSL2 - detect Windows and provide WSL setup instructions
- Consider creating a companion `reset.sh` script to clean up installations for testing
