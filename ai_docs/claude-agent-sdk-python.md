# Claude Agent SDK Reference - Python

Source: https://docs.claude.com/en/api/agent-sdk/python

---

## Overview

The Python Agent SDK provides two primary interaction models with Claude Code:

### Installation

```bash
pip install claude-agent-sdk
```

## Choosing Between query() and ClaudeSDKClient

### Quick Comparison

| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| Session | New each time | Reuses same session |
| Memory | No conversation history | Maintains context |
| Interrupts | Not supported | Supported |
| Custom tools | Not available | Available via `@tool` decorator |

### When to Use query() (New Session Each Time)

Use the `query()` function when:
- You need a one-off task without conversation memory
- Each interaction is independent
- You don't need to interrupt execution
- You don't require custom tools

### When to Use ClaudeSDKClient (Continuous Conversation)

Use `ClaudeSDKClient` when:
- You need persistent session state across multiple exchanges
- Claude should remember context from previous interactions
- You need to interrupt execution mid-task
- You want to define custom tools via the `@tool` decorator

## Functions

### query()

Creates a new session for each interaction, returning an async iterator of messages. Best for one-off tasks without conversation memory.

#### Parameters

- `prompt` (str | AsyncIterator[str]): The user's message or streaming input
- `options` (ClaudeAgentOptions, optional): Configuration options

#### Returns

AsyncIterator[Message]: Stream of messages from the agent

#### Example - With options

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    "Analyze this code",
    ClaudeAgentOptions(
        system_prompt="You are a code reviewer",
        permission_mode="acceptEdits"
    )
):
    print(message)
```

### tool()

Decorator for creating custom MCP tools with type-safe schemas.

#### Parameters

- `name` (str, optional): Tool name
- `description` (str, optional): Tool description  
- `input_schema` (dict | Type, optional): JSON schema or Python type

#### Input Schema Options

You can define the input schema in multiple ways:
1. JSON Schema dict
2. Python dataclass
3. Pydantic model

#### Returns

Callable decorator that wraps the function

#### Example

```python
from claude_agent_sdk import tool
from dataclasses import dataclass

@dataclass
class SearchParams:
    query: str
    max_results: int = 10

@tool(
    name="web_search",
    description="Search the web for information",
    input_schema=SearchParams
)
async def search_web(query: str, max_results: int = 10):
    # Implementation
    return {"results": []}
```

### create_sdk_mcp_server()

Creates an in-process MCP server hosting custom tools.

#### Parameters

- `tools` (list[SdkMcpTool]): List of tool functions decorated with `@tool`

#### Returns

McpSdkServerConfig: Configuration object for the MCP server

#### Example

```python
from claude_agent_sdk import create_sdk_mcp_server, tool

@tool(name="calculator")
async def calculate(expression: str):
    return eval(expression)

mcp_server = create_sdk_mcp_server([calculate])
```

## Classes

### ClaudeSDKClient

Maintains persistent session state across multiple exchanges, enabling continuous conversations where Claude remembers context.

#### Key Features

- Persistent session management
- Conversation history
- Interrupt support
- Custom tool integration

#### Methods

**connect()**
- Establishes connection to the Claude Code CLI
- Must be called before sending queries

**disconnect()**
- Closes the connection and cleans up resources

**query(prompt, options)**
- Sends a message in streaming mode
- Parameters:
  - `prompt`: User message or async iterator
  - `options`: ClaudeAgentOptions configuration
- Returns: AsyncIterator[Message]

**receive_messages()**
- Processes all responses from a query
- Returns: list[Message]

**interrupt()**
- Stops execution mid-task
- Only works with active session

#### Context Manager Support

```python
async with ClaudeSDKClient() as client:
    async for message in client.query("Hello"):
        print(message)
```

#### Example - Continuing a conversation

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # First message
    messages1 = []
    async for msg in client.query("What is 2+2?"):
        messages1.append(msg)
    
    # Follow-up (remembers context)
    messages2 = []
    async for msg in client.query("What about 3+3?"):
        messages2.append(msg)
```

#### Example - Streaming input with ClaudeSDKClient

```python
async def stream_user_input():
    yield "Please analyze "
    await asyncio.sleep(1)
    yield "this code: "
    await asyncio.sleep(1)
    yield "def hello(): print('world')"

async with ClaudeSDKClient() as client:
    async for message in client.query(stream_user_input()):
        print(message)
```

#### Example - Using interrupts

```python
async with ClaudeSDKClient() as client:
    task = asyncio.create_task(
        client.receive_messages(client.query("Long running task"))
    )
    
    await asyncio.sleep(5)
    await client.interrupt()  # Stop execution
    
    messages = await task
```

#### Example - Advanced permission control

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient() as client:
    async for message in client.query(
        "Refactor this code",
        ClaudeAgentOptions(
            permission_mode="plan",  # Require approval for changes
            allowed_tools=["read", "grep"],  # Limit available tools
            system_prompt="You are a careful code reviewer"
        )
    ):
        print(message)
```

## Types

### SdkMcpTool

Type alias for tool functions decorated with `@tool`.

### ClaudeAgentOptions

Configuration dataclass supporting:

- `allowed_tools` (list[str], optional): Whitelist of tools Claude can use
- `disallowed_tools` (list[str], optional): Blacklist of tools Claude cannot use
- `system_prompt` (str | SystemPromptPreset, optional): System prompt or preset
- `permission_mode` (PermissionMode, optional): Permission control mode
- `mcp_servers` (list[McpServerConfig], optional): Custom tool servers
- `hooks` (dict, optional): Event interception hooks
- `setting_sources` (list[SettingSource], optional): Configuration sources
- `subagents` (list[AgentDefinition], optional): Specialized sub-agents

### SystemPromptPreset

Predefined system prompts:
- `"default"`: Standard Claude Code behavior
- `"concise"`: Brief responses
- `"detailed"`: Comprehensive responses

### SettingSource

Source for loading settings: `"user"` | `"project"` | `"local"`

#### Default behavior

When `setting_sources` is not specified, the SDK loads settings from all available sources in this order:
1. User settings (`~/.claude/settings.json`)
2. Project settings (`.claude/settings.json`)
3. Local settings (`.claude.local/settings.json`)

#### Why use setting_sources?

Use `setting_sources` to:
- **Isolate tests**: Prevent test runs from using your personal settings
- **Control config**: Explicitly choose which settings files to load
- **Ensure reproducibility**: Guarantee consistent behavior across environments

####  Settings precedence

Settings are loaded in the order specified, with later sources overriding earlier ones:

```python
ClaudeAgentOptions(
    setting_sources=["user", "project"]  # project overrides user
)
```

### AgentDefinition

Defines specialized sub-agents with specific capabilities:

```python
{
    "name": "code_reviewer",
    "system_prompt": "You review code for bugs",
    "allowed_tools": ["read", "grep"]
}
```

### PermissionMode

Controls how Claude uses tools:
- `"default"`: Ask for permission for sensitive operations
- `"acceptEdits"`: Auto-approve file edits
- `"plan"`: Require approval for all actions
- `"bypassPermissions"`: Skip all permission checks (use with caution)

### McpSdkServerConfig

Configuration for in-process MCP server created with `create_sdk_mcp_server()`.

### McpServerConfig

Base configuration for MCP servers.

### McpStdioServerConfig

Configuration for stdio-based MCP servers:

```python
{
    "type": "stdio",
    "command": "python",
    "args": ["server.py"],
    "env": {"API_KEY": "..."}
}
```

### McpSSEServerConfig

Configuration for Server-Sent Events MCP servers:

```python
{
    "type": "sse",
    "url": "http://localhost:3000/sse"
}
```

### McpHttpServerConfig

Configuration for HTTP-based MCP servers:

```python
{
    "type": "http",
    "url": "http://localhost:3000",
    "headers": {"Authorization": "Bearer ..."}
}
```

## Message Types

### Message

Base type for all messages. Union of: `UserMessage | AssistantMessage | SystemMessage | ResultMessage`

### UserMessage

Message from the user to Claude:

```python
{
    "role": "user",
    "content": "Hello Claude"
}
```

### AssistantMessage

Message from Claude with content blocks:

```python
{
    "role": "assistant",
    "content": [
        {"type": "text", "text": "Hello!"},
        {"type": "thinking", "thinking": "User greeted me..."},
        {"type": "tool_use", "name": "read", "input": {...}}
    ]
}
```

### SystemMessage

System-level message for configuration:

```python
{
    "role": "system",
    "content": "You are a helpful assistant"
}
```

### ResultMessage

Final message with usage and cost data:

```python
{
    "type": "result",
    "usage": {
        "input_tokens": 100,
        "output_tokens": 50
    },
    "cost": {
        "input_cost": 0.001,
        "output_cost": 0.002
    }
}
```

## Content Block Types

### ContentBlock

Base type for content blocks. Union of: `TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock`

### TextBlock

Plain text content:

```python
{
    "type": "text",
    "text": "This is a response"
}
```

### ThinkingBlock

Claude's internal reasoning (Extended Thinking):

```python
{
    "type": "thinking",
    "thinking": "Let me analyze this step by step..."
}
```

### ToolUseBlock

Claude requesting to use a tool:

```python
{
    "type": "tool_use",
    "id": "toolu_123",
    "name": "read_file",
    "input": {"file_path": "/path/to/file"}
}
```

### ToolResultBlock

Result from tool execution:

```python
{
    "type": "tool_result",
    "tool_use_id": "toolu_123",
    "content": "File contents here",
    "is_error": false
}
```

## Hooks

Hooks allow you to intercept events during agent execution:

### Available Hooks

- `PreToolUse`: Before a tool is executed
- `PostToolUse`: After a tool completes
- `UserPromptSubmit`: When user submits input

### Example

```python
from claude_agent_sdk import ClaudeAgentOptions

async def on_tool_use(tool_name, tool_input):
    print(f"Using tool: {tool_name}")
    return True  # Allow execution

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": on_tool_use
    }
)
```

## Error Handling

SDK provides specialized exceptions:

- `CLINotFoundError`: Claude Code CLI not found in PATH
- `CLIConnectionError`: Failed to connect to CLI
- `ProcessError`: CLI process exited unexpectedly
- `CLIJSONDecodeError`: Invalid JSON from CLI

### Example

```python
from claude_agent_sdk import ClaudeSDKClient, CLINotFoundError

try:
    async with ClaudeSDKClient() as client:
        async for msg in client.query("Hello"):
            print(msg)
except CLINotFoundError:
    print("Please install Claude Code CLI")
except Exception as e:
    print(f"Error: {e}")
```

## Advanced Features

### Streaming Input

Both `query()` and `ClaudeSDKClient.query()` accept async iterables for dynamic prompts:

```python
async def generate_prompt():
    yield "First part"
    await asyncio.sleep(1)
    yield "Second part"

async for message in query(generate_prompt()):
    print(message)
```

### Custom Tool Integration

Create your own tools and integrate them via MCP:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(name="database_query", description="Query the database")
async def query_db(sql: str):
    # Your database logic
    return {"rows": []}

mcp_server = create_sdk_mcp_server([query_db])

async with ClaudeSDKClient() as client:
    async for msg in client.query(
        "Get all users from database",
        ClaudeAgentOptions(mcp_servers=[mcp_server])
    ):
        print(msg)
```

### Subagents

Define specialized agents for specific tasks:

```python
options = ClaudeAgentOptions(
    subagents=[
        {
            "name": "security_scanner",
            "system_prompt": "You scan code for security issues",
            "allowed_tools": ["read", "grep"]
        },
        {
            "name": "formatter",
            "system_prompt": "You format code",
            "allowed_tools": ["read", "edit"]
        }
    ]
)
```

---

**Note**: This documentation is based on the Claude Agent SDK for Python. For TypeScript documentation, see the [TypeScript SDK reference](https://docs.claude.com/en/api/agent-sdk/typescript).

For more examples and guides, visit:
- [Agent SDK Overview](https://docs.claude.com/en/api/agent-sdk/overview)
- [Migration Guide](https://docs.claude.com/en/docs/claude-code/sdk/migration-guide)
- [Handling Permissions](https://docs.claude.com/en/docs/claude-code/sdk/sdk-permissions)
- [Slash Commands](https://docs.claude.com/en/docs/claude-code/sdk/sdk-slash-commands)
