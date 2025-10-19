# Claude Code Slash Commands

## Overview

Slash commands in Claude Code enable users to manage behavior during interactive sessions. The system supports built-in commands, custom user-defined commands, plugin commands, and integrations with MCP servers.

## Built-in Commands

Claude Code provides approximately 25 native commands including:

- **Session management**: `/clear`, `/rewind`, `/compact`
- **Configuration**: `/config`, `/status`, `/settings`
- **Account**: `/login`, `/logout`
- **Development**: `/review`, `/bug`, `/terminal-setup`
- **Model control**: `/model`
- **Advanced features**: `/sandbox`, `/vim`, `/mcp`

As one example, the `/cost` command displays "token usage statistics (see cost tracking guide for subscription-specific details)."

## Custom Slash Commands

Users can create personalized commands through Markdown files organized in two locations:

**Project-level commands** reside in `.claude/commands/` and are shared with teams.

**User-level commands** live in `~/.claude/commands/` and remain personal across all projects.

### Command Structure

Commands use the syntax `/<command-name> [arguments]`. The filename (minus `.md` extension) becomes the command name.

### Dynamic Arguments

Commands support argument placeholders:

- `$ARGUMENTS` captures all arguments collectively
- `$1`, `$2`, etc., reference specific positional arguments

For instance, a command definition might specify: "Review PR #$1 with priority $2 and assign to $3."

### Advanced Features

**Namespacing**: Commands organized in subdirectories appear with directory context in help text. A file at `.claude/commands/frontend/component.md` creates `/component` displaying "(project:frontend)".

**Bash execution**: Commands can execute shell commands using the `!` prefix, including output in context.

**File references**: Use the `@` prefix to include file contents within commands.

**Extended thinking**: Commands can trigger extended thinking by including relevant keywords.

### Frontmatter Configuration

Command files support metadata fields:

- `description`: Brief command overview
- `allowed-tools`: Specifies available tools
- `argument-hint`: Shows expected arguments during autocompletion
- `model`: Designates specific AI model
- `disable-model-invocation`: Prevents SlashCommand tool execution

## Plugin Commands

Plugins distribute custom slash commands through marketplaces. Plugin commands:

- Use namespacing format: `/plugin-name:command-name`
- Become available automatically after installation
- Support all standard command features
- Integrate seamlessly with the ecosystem

## MCP Slash Commands

MCP servers expose prompts as slash commands using the pattern: `/mcp__<server-name>__<prompt-name> [arguments]`

Features include dynamic discovery, argument support, and automatic availability when servers connect successfully.

The `/mcp` command manages server connections and OAuth authentication.

## SlashCommand Tool

This tool allows Claude to programmatically invoke custom commands during conversations. It only executes user-defined commands with populated `description` fields.

Users can disable specific commands using `disable-model-invocation: true` in frontmatter or deny SlashCommand tool access entirely via permission settings.

## Slash Commands vs. Agent Skills

These serve distinct purposes:

**Slash commands** suit quick, frequently-used prompts fitting single files. Examples include simple review or optimization templates requiring manual invocation.

**Agent Skills** accommodate complex workflows spanning multiple files with automatic discovery. They include scripts, reference documentation, and standardized team processes.

Key distinction: "slash commands are manually invoked; skills are automatically discovered based on context."

## Management and Permissions

Permission rules support exact matches (`SlashCommand:/commit`) and prefix patterns (`SlashCommand:/review-pr:*`).

A character budget limits command description sizes in context, preventing token overflow. The default limit is 15,000 characters, customizable via the `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable.
