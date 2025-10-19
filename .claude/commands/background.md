---
description: Fires off a full Claude Code instance in the background
argument-hint: [prompt] [model] [report-file]
allowed-tools: Bash, BashOutput, Read, Edit, MultiEdit, Write, Grep, Glob, WebFetch, WebSearch, TodoWrite, Task
---

# Background Claude Code

Run a Claude Code instance in the background to perform tasks autonomously while you continue working.

## Variables

USER_PROMPT: $1
MODEL: $2 (defaults to 'sonnet' if not provided)
REPORT_FILE: $3 (defaults to './agents/background/background-report-DAY-NAME_HH_MM_SS.md' if not provided)

## Instructions

- Capture timestamp in a variable FIRST to ensure consistency across file creation and references
- Create the initial report file with header BEFORE launching the background agent
- Fire off a new Claude Code instance using the Bash tool with run_in_background=true
- IMPORTANT: Pass the `USER_PROMPT` exactly as provided with no modifications
- Set the model to either 'sonnet' or 'opus' based on `MODEL` parameter
- Configure Claude Code with all necessary flags for automated operation
- All report format instructions are embedded in the --append-system-prompt
- Use --print flag to run in non-interactive mode
- Use --output-format text for standard text output
- Use --dangerously-skip-permissions to bypass permission prompts for automated operation
- Use all provided cli flags AS IS. Do not alter them.

## Workflow

1. Create the report directory if it doesn't exist:

```bash
mkdir -p agents/background
```

2. Set default values for parameters:
   - `MODEL`
   - `TIMESTAMP` (capture once for consistency)
   - `REPORT_FILE` (using the captured timestamp)

3. Create the initial report file with just the header (IMPORTANT: Only IF no report file is provided - if it is provided, echo it and skip this step):

   Get this into your context window so you know what to pass into the Claude Code command.

```bash
TIMESTAMP=$(date +%a_%H_%M_%S)
echo "TIMESTAMP: ${TIMESTAMP}"
REPORT_FILE="${REPORT_FILE:-.}/agents/background/background-report-${TIMESTAMP}.md}"
echo "REPORT_FILE: ${REPORT_FILE}"
echo "# Background Agent Report - ${TIMESTAMP}" > "${REPORT_FILE}"
```

<primary-agent-delegation>
4. Construct the Claude Code command with all settings:

   - Execute the command using Bash with run_in_background=true

```bash
claude \
  --model "${MODEL}" \
  --output-format text \
  --dangerously-skip-permissions \
  --append-system-prompt "IMPORTANT: You are running as a background agent. Your primary responsibility is to execute work and document your progress continuously in ${REPORT_FILE}. Iteratively write to the report file continuously as you work. Every few tool calls you should update the REPORT_FILE ## Progress section. Follow this file structure.

## CRITICAL WORKFLOW STRUCTURE

   IMPORTANT: You MUST follow this workflow as you work:

   1. The file ${REPORT_FILE} has been created with a header. You must UPDATE as you proceed it (not recreate it) with this EXACT markdown structure:

```markdown
# Background Agent Report - DAY-NAME_HH_MM_SS

## Task Understanding
Clearly state what the user requested. Break down complex requests into numbered items:
User requested:
1. [Item 1]
2. [Item 2]
...

## Analysis
Your analysis of the task, codebase exploration, key findings, etc.

## Progress
Update this section FREQUENTLY as you work. Use bullet points:
- [timestamp or step] Completed X
- [timestamp or step] Working on Y
- [timestamp or step] Found Z
...

## Code Changes
Document all files modified, created, or deleted:
- `path/to/file.ext`: Description of changes
- `path/to/other.ext`: Description of changes

## Results
Final outcomes, test results, verification steps completed

## Issues Encountered
Any problems, blockers, or warnings (if none, state 'None')

## Next Steps
If task is complete: State 'Task complete'
If blocked: Describe what's needed to proceed
If partially complete: List remaining work
```

   2. Write to the report file FREQUENTLY throughout your work:
      - After completing each major step
      - When you discover important information
      - Before and after making code changes
      - When encountering issues

   3. Use the Edit tool to update existing sections (never recreate the entire file)

   4. When you finish your work:
      - If successful: Rename ${REPORT_FILE} to ${REPORT_FILE.md}.complete.md
      - If failed/blocked: Rename ${REPORT_FILE} to ${REPORT_FILE.md}.failed.md

   Remember: The report is your PRIMARY output. Update it frequently and thoroughly.
" \
  --print "${USER_PROMPT}"
```

</primary-agent-delegation>

1. After you kick off the background agent, use the BashOutput tool to check the status of the background agent
   - If something goes wrong investigate and report back to the user
   - If everything is working fine, continue to the `Response to User` section

## Response to User

After launching the background agent, respond with:

```
Background Claude Code kicked off. Agent is writing to `REPORT_FILE` as it works.
When it completes it will rename the file to `REPORT_FILE.complete.md` on success or `REPORT_FILE.failed.md` if it fails.
```
