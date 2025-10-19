# Claude Code SDK - Headless Mode

## Overview

Headless mode enables you to execute Claude Code programmatically from command-line scripts and automation workflows without requiring any interactive graphical interface. This capability integrates with your existing automation infrastructure seamlessly.

## Basic Usage

The primary entry point is the `claude` command with the `--print` (or `-p`) flag to operate in non-interactive mode:

```bash
claude -p "Stage my changes and write a set of commits for them" \
  --allowedTools "Bash,Read" \
  --permission-mode acceptEdits
```

## Configuration Options

### Key CLI Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--print`, `-p` | Non-interactive execution | `claude -p "query"` |
| `--output-format` | Result format (text, json, stream-json) | `claude -p --output-format json` |
| `--resume`, `-r` | Resume by session ID | `claude --resume abc123` |
| `--continue`, `-c` | Continue most recent session | `claude --continue` |
| `--verbose` | Enable detailed logging | `claude --verbose` |
| `--append-system-prompt` | Extend system instructions | `claude --append-system-prompt "Custom instruction"` |
| `--allowedTools` | Permitted tools (space or comma-separated) | `claude --allowedTools "Bash(npm),mcp__filesystem"` |
| `--disallowedTools` | Restricted tools | `claude --disallowedTools "Bash(git),mcp__github"` |
| `--mcp-config` | MCP server configuration file | `claude --mcp-config servers.json` |
| `--permission-prompt-tool` | MCP tool for permission handling | `claude --permission-prompt-tool mcp__auth__prompt` |

## Multi-Turn Conversations

Continue previous conversations using session management:

```bash
# Continue the most recent session
claude --continue "Now refactor this for better performance"

# Resume specific conversation by ID
claude --resume 550e8400-e29b-41d4-a716-446655440000 "Update the tests"

# Resume in non-interactive mode
claude --resume 550e8400-e29b-41d4-a716-446655440000 "Fix linting" --no-interactive
```

## Output Formats

### Text Output (Default)

Returns plain text results:

```bash
claude -p "Explain file src/components/Header.tsx"
```

### JSON Output

Provides structured metadata alongside results:

```bash
claude -p "How does the data layer work?" --output-format json
```

Returns:

```json
{
  "type": "result",
  "subtype": "success",
  "total_cost_usd": 0.003,
  "is_error": false,
  "duration_ms": 1234,
  "duration_api_ms": 800,
  "num_turns": 6,
  "result": "The response text here...",
  "session_id": "abc123"
}
```

### Streaming JSON Output

Emits each message as received:

```bash
claude -p "Build an application" --output-format stream-json
```

Conversation structure: initial system message → user/assistant exchanges → final result message with statistics.

## Input Formats

### Text Input (Default)

```bash
# Direct argument
claude -p "Explain this code"

# Via stdin
echo "Explain this code" | claude -p
```

### Streaming JSON Input

Provide multiple conversation turns via stdin using JSONL format:

```bash
echo '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"Explain this code"}]}}' \
  | claude -p --output-format=stream-json --input-format=stream-json --verbose
```

Requires `-p` and `--output-format stream-json` flags.

## Integration Examples

### SRE Incident Response

```bash
#!/bin/bash
investigate_incident() {
    local incident_description="$1"
    local severity="${2:-medium}"

    claude -p "Incident: $incident_description (Severity: $severity)" \
      --append-system-prompt "You are an SRE expert. Diagnose the issue, assess impact, and provide immediate action items." \
      --output-format json \
      --allowedTools "Bash,Read,WebSearch,mcp__datadog" \
      --mcp-config monitoring-tools.json
}

investigate_incident "Payment API returning 500 errors" "high"
```

### Automated Security Review

```bash
audit_pr() {
    local pr_number="$1"

    gh pr diff "$pr_number" | claude -p \
      --append-system-prompt "Review for vulnerabilities, insecure patterns, and compliance issues." \
      --output-format json \
      --allowedTools "Read,Grep,WebSearch"
}

audit_pr 123 > security-report.json
```

### Multi-Turn Legal Assistant

```bash
# Persistent session for document review
session_id=$(claude -p "Start legal review session" --output-format json | jq -r '.session_id')

claude -p --resume "$session_id" "Review contract.pdf for liability clauses"
claude -p --resume "$session_id" "Check GDPR compliance"
claude -p --resume "$session_id" "Generate executive summary"
```

## Best Practices

**JSON Parsing**: Use structured output for programmatic processing:

```bash
result=$(claude -p "Generate code" --output-format json)
code=$(echo "$result" | jq -r '.result')
cost=$(echo "$result" | jq -r '.total_cost_usd')
```

**Error Handling**: Check exit codes and capture stderr:

```bash
if ! claude -p "$prompt" 2>error.log; then
    echo "Error occurred:" >&2
    cat error.log >&2
    exit 1
fi
```

**Session Management**: Preserve context across multiple turns for complex workflows.

**Timeouts**: Implement safeguards for extended operations:

```bash
timeout 300 claude -p "$complex_prompt" || echo "Timed out after 5 minutes"
```

**Rate Limiting**: Add delays between consecutive requests to respect API quotas.

---

**Source:** https://docs.claude.com/en/docs/claude-code/sdk/sdk-headless
