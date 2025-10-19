# Claude Code Configuration Guide
> A practical guide to the three-layer configuration system

---

## Quick Reference: Configuration Priority

```
┌─────────────────────────────────────┐
│   Project Level (./.claude/)        │  ← HIGHEST Priority
│   • Team conventions                │
│   • Project-specific tools          │
│   • Security policies               │
└─────────────────────────────────────┘
            ↓ overrides
┌─────────────────────────────────────┐
│   User Global (~/.claude/CLAUDE.md) │  ← MEDIUM Priority
│   • Personal coding style           │
│   • Preferred libraries             │
│   • Communication preferences       │
└─────────────────────────────────────┘
            ↓ overrides
┌─────────────────────────────────────┐
│   System Level (Built-in)           │  ← LOWEST Priority
│   • Default behaviors               │
│   • Safety policies                 │
│   • Core functionality              │
└─────────────────────────────────────┘
```

**Rule**: Most specific wins. Project > User > System.

---

## The Three Layers Explained

### 1. System Level (Built-in)
**What it is**: Claude Code's default behavior
**Where it lives**: Inside the application (you can't edit it)
**What it does**:
- Ensures safety (defensive security only)
- Defines default tool behaviors
- Provides baseline instructions

**Your action**: Trust it. Don't fight it.

---

### 2. User Global Level
**What it is**: Your personal preferences across ALL projects
**Where it lives**: `~/.claude/CLAUDE.md`
**What it does**:
- Applies your coding style everywhere
- Sets language/framework preferences
- Defines your communication style

**Your action**: Define once, use everywhere.

---

### 3. Project Level
**What it is**: Project-specific customizations
**Where it lives**: `./.claude/` directory in project root
**What it does**:
- Overrides user/system settings
- Adds custom commands (slash commands)
- Enforces team conventions

**Your action**: Customize per project, commit to git.

---

## Decision Tree: What Goes Where?

### Start Here
**Question**: Does this apply to ALL my projects?

**YES** → User Global (`~/.claude/CLAUDE.md`)
- Examples: "Use lodash/fp", "Prefer functional programming", "Use TCL logging format"

**NO** → Continue to next question

---

**Question**: Is this specific to THIS project or team?

**YES** → Project Level (`./.claude/`)
- Examples: "Use microservices pattern", "Run ESLint before commits", "Deploy with ./scripts/deploy.sh"

**NO** → It's probably a system default, no config needed

---

## What to Put in User Global

### ✅ DO Put Here:
```markdown
# ~/.claude/CLAUDE.md

## Code Style (applies everywhere)
- Use functional programming
- Prefer composition over inheritance
- Use strict typing

## Libraries (my preferred tools)
- JavaScript: Use lodash/fp
- Validation: Use io-ts decoders
- HTTP: Use node-fetch

## Debug Patterns (my logging style)
console.log('TCL ------>', variable, JSON.stringify(data, null, 4))

## Communication Preferences
- Be concise
- Use emojis for status: ✅ ❌ 🔧
- Focus on technical improvements
```

### ❌ DON'T Put Here:
- Project-specific architecture ("Use microservices in this app")
- Team conventions ("All commits must have JIRA tickets")
- Project file references ("Read ./docs/API.md first")
- Deployment procedures ("Deploy to staging with script X")

---

## What to Put in Project Level

### ✅ DO Put Here:

#### A. Project Instructions (`./.claude/CLAUDE.md` or `instructions.md`)
```markdown
# Project TAC-4 - Claude Instructions

## Architecture
- Microservices with event sourcing
- Shared kernel in /packages/core
- Use domain-driven design

## Key Conventions
- All API routes in /src/routes
- Tests colocated with source files
- Use Zod for runtime validation

## Build & Deploy
- Run `npm run build` before committing
- Deploy with `./scripts/deploy.sh <env>`
```

#### B. Custom Slash Commands (`./.claude/commands/*.md`)
```markdown
# /deploy command
Deploy the application to specified environment

Steps:
1. Run tests
2. Build production bundle
3. Execute ./scripts/deploy.sh $ARGUMENTS
4. Report deployment status
```

#### C. Project Settings (`./.claude/settings.json`)
```json
{
  "permissions": {
    "allow": [
      "Bash(npm:*)",
      "Bash(./scripts/*:*)",
      "Write"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)"
    ]
  }
}
```

#### D. Hooks (`./.claude/hooks/*.py`)
- Security validation
- Environment protection
- Custom workflows

### ❌ DON'T Put Here:
- Personal preferences that apply to all projects
- Your general coding philosophy
- Language-specific preferences (unless project mandates different from your norm)

---

## Practical Examples

### Example 1: Logging Style
**Situation**: You always want logs in a specific format

**Decision**: User Global
**Why**: Same format wanted across all projects
**Where**: `~/.claude/CLAUDE.md`
```markdown
## Debugging
Use this log format:
console.log('TCL ------>', variable, JSON.stringify(data, null, 4))
```

---

### Example 2: Deployment Command
**Situation**: This project has a unique deployment script

**Decision**: Project Level
**Why**: Specific to this project only
**Where**: `./.claude/commands/deploy.md`
```markdown
Run deployment:
1. npm run build
2. ./scripts/deploy.sh staging
3. Report git diff --stat
```

---

### Example 3: TypeScript Strict Mode
**Situation**: You always want strict TypeScript

**Decision**: User Global
**Why**: Your personal standard for quality
**Where**: `~/.claude/CLAUDE.md`
```markdown
## TypeScript
- Always use strict mode
- Enable all strict flags
- No implicit any
```

---

### Example 4: Monorepo Structure
**Situation**: This project is a monorepo with specific package organization

**Decision**: Project Level
**Why**: Architecture specific to this codebase
**Where**: `./.claude/CLAUDE.md` (project)
```markdown
## Monorepo Structure
- /packages/core - Shared utilities
- /packages/web - Frontend app
- /packages/api - Backend services

Always check dependencies before cross-package imports.
```

---

## Configuration Checklist

### Setting Up User Global
1. Create `~/.claude/CLAUDE.md` if it doesn't exist
2. Add your coding philosophy
3. Define preferred libraries/tools
4. Set communication preferences
5. Include debug/logging patterns

### Setting Up Project Level
1. Create `./.claude/` directory
2. Add `settings.json` for permissions
3. Create custom commands in `commands/*.md`
4. Add project instructions (optional)
5. Implement hooks if needed (advanced)
6. **Commit to git** so team benefits

---

## Common Patterns

### Pattern: The "Clean Up" Workflow
**User Global Setup**:
```markdown
## Workflow Pattern: Edit → Clean Up → Continue

When asked to "clean up":
1. Fix syntax errors
2. Remove unused imports/variables
3. Improve type safety
4. Optimize performance
5. No need to ask permission
```

**Result**: Works across all projects automatically.

---

### Pattern: Project-Specific Testing
**Project Level Setup** (`./.claude/commands/test.md`):
```markdown
Run project tests:
1. npm run test:unit
2. npm run test:integration
3. npm run test:e2e
4. Report any failures with details
```

**Result**: `/test` command available in this project only.

---

### Pattern: Security Guardrails
**Project Level Setup** (`./.claude/settings.json`):
```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)"
    ]
  }
}
```

**Project Level Hook** (`./.claude/hooks/pre_tool_use.py`):
```python
# Block access to .env files
if '.env' in file_path and not file_path.endswith('.env.sample'):
    print("BLOCKED: Access to .env prohibited")
    sys.exit(2)
```

**Result**: Project-specific security policies enforced automatically.

---

## Advanced: Project Settings Reference

### Permissions Structure
```json
{
  "permissions": {
    "allow": [
      "Bash(npm:*)",        // All npm commands
      "Bash(./scripts/*:*)", // Project scripts
      "Write",               // File creation
      "Bash(ls:*)"          // Safe reads
    ],
    "deny": [
      "Bash(rm -rf:*)",           // Destructive operations
      "Bash(git push --force:*)"  // Force pushes
    ]
  }
}
```

### Hooks System
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python .claude/hooks/pre_tool_use.py"
      }]
    }],
    "PostToolUse": [/* validation */],
    "Notification": [/* alerts */],
    "Stop": [/* cleanup */]
  }
}
```

---

## Quick Start Templates

### Minimal User Global
```markdown
# ~/.claude/CLAUDE.md

## Core Principles
- Write clean, maintainable code
- Use functional programming when possible
- Prefer explicit over implicit

## Communication
- Be concise
- Focus on technical accuracy
```

### Minimal Project Setup
```bash
mkdir -p .claude/commands
touch .claude/settings.json
touch .claude/commands/test.md
```

**.claude/settings.json**:
```json
{
  "permissions": {
    "allow": ["Bash(npm:*)", "Write"],
    "deny": ["Bash(rm -rf:*)"]
  }
}
```

**.claude/commands/test.md**:
```markdown
Run tests and report results:
npm test
```

---

## Troubleshooting

### Issue: Configuration Not Working
**Check**:
1. File location correct? (`~/.claude/CLAUDE.md` vs `./.claude/`)
2. Syntax valid? (Markdown formatting)
3. Conflicting rules? (Project overrides user)

### Issue: Hook Blocking Everything
**Check**:
1. Hook exit codes (0 = pass, 2 = block)
2. Pattern matching logic
3. Error messages in stderr

### Issue: Slash Command Not Found
**Check**:
1. File in `./.claude/commands/`?
2. File has `.md` extension?
3. Restart Claude Code session?

---

## Best Practices Summary

### DO:
✅ Start minimal, add as needed
✅ Commit `./.claude/` to version control
✅ Document custom commands
✅ Use project-level for team standards
✅ Use user-global for personal preferences
✅ Keep hooks simple and fast

### DON'T:
❌ Duplicate settings across levels
❌ Put project specifics in user-global
❌ Put personal preferences in project config
❌ Over-configure early
❌ Store secrets in configuration
❌ Make hooks complex or slow

---

## Configuration Flow Chart

```
New Task Arrives
       ↓
Does System Block It? ──YES──→ Stop (Security Policy)
       ↓ NO
       ↓
Check Project Config (./.claude/)
       ↓
Project Rules Apply ──YES──→ Follow Project Rules
       ↓ NO/PARTIAL              (Highest Priority)
       ↓
Check User Global (~/.claude/CLAUDE.md)
       ↓
User Preferences Apply ──YES──→ Follow User Preferences
       ↓ NO                       (Medium Priority)
       ↓
Use System Defaults
(Lowest Priority)
```

---

## Real-World Setup (Your Current Config)

### Your User Global Highlights
- **Workflow**: Edit → Clean Up → Continue pattern
- **Style**: Functional programming, strict typing
- **Libraries**: lodash/fp, io-ts, node-fetch
- **Logging**: `console.log('TCL ------>', ...)`
- **Communication**: Concise, emoji status, technical focus

### Your Project Level Highlights
- **Commands**: 13 custom slash commands (/start, /prime, /implement, etc.)
- **Security**: Blocks .env access, dangerous rm commands
- **Permissions**: Allow safe operations, deny destructive ones
- **Hooks**: PreToolUse validation, session logging, notifications
- **Sophistication**: Advanced setup with audit trails

### Result
A **mature, well-architected system** balancing:
- Productivity (custom commands)
- Safety (hooks + permissions)
- Team collaboration (version-controlled config)
- Personal efficiency (user-global preferences)

---

## Key Takeaways

1. **Three layers, three purposes**:
   - System = Safety baseline
   - User = Personal style
   - Project = Team conventions

2. **Priority is hierarchical**:
   - Project > User > System
   - Most specific wins

3. **Configuration is about boundaries**:
   - User-global: "How I work"
   - Project-level: "How WE work on THIS"

4. **Start simple, evolve intentionally**:
   - Don't over-configure upfront
   - Add patterns as they emerge
   - Refactor reusable patterns up to user-global

5. **Version control matters**:
   - Commit `./.claude/` to share with team
   - Keep `~/.claude/` private

---

## Further Reading

- Claude Code Docs: https://docs.claude.com/en/docs/claude-code
- Slash Commands Guide: Check `.claude/commands/` examples
- Hooks Reference: Review `.claude/hooks/` implementations
- Settings Schema: Examine `.claude/settings.json` structure

---

**Remember**: Configuration should serve you, not constrain you. Start minimal, add value incrementally, and keep it maintainable.
