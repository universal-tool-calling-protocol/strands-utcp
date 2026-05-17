# strands-utcp

[![Awesome Strands Agents](https://img.shields.io/badge/Awesome-Strands%20Agents-00FF77?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjkwIiBoZWlnaHQ9IjQ2MyIgdmlld0JveD0iMCAwIDI5MCA0NjMiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05Ny4yOTAyIDUyLjc4ODRDODUuMDY3NCA0OS4xNjY3IDcyLjIyMzQgNTYuMTM4OSA2OC42MDE3IDY4LjM2MTZDNjQuOTgwMSA4MC41ODQzIDcxLjk1MjQgOTMuNDI4MyA4NC4xNzQ5IDk3LjA1MDFMMjM1LjExNyAxMzkuNzc1QzI0NS4yMjMgMTQyLjc2OSAyNDYuMzU3IDE1Ni42MjggMjM2Ljg3NCAxNjEuMjI2TDMyLjU0NiAyNjAuMjkxQy0xNC45NDM5IDI4My4zMTYgLTkuMTYxMDcgMzUyLjc0IDQxLjQ4MzUgMzY3LjU5MUwxODkuNTUxIDQxMS4wMDlMMTkwLjEyNSA0MTEuMTY5QzIwMi4xODMgNDE0LjM3NiAyMTQuNjY1IDQwNy4zOTYgMjE4LjE5NiAzOTUuMzU1QzIyMS43ODQgMzgzLjEyMiAyMTQuNzc0IDM3MC4yOTYgMjAyLjU0MSAzNjYuNzA5TDU0LjQ3MzggMzIzLjI5MUM0NC4zNDQ3IDMyMC4zMjEgNDMuMTg3OSAzMDYuNDM2IDUyLjY4NTcgMzAxLjgzMUwyNTcuMDE0IDIwMi43NjZDMzA0LjQzMiAxNzkuNzc2IDI5OC43NTggMTEwLjQ4MyAyNDguMjMzIDk1LjUxMkw5Ny4yOTAyIDUyLjc4ODRaIiBmaWxsPSIjRkZGRkZGIi8+CjxwYXRoIGQ9Ik0yNTkuMTQ3IDAuOTgxODEyQzI3MS4zODkgLTIuNTc0OTggMjg0LjE5NyA0LjQ2NTcxIDI4Ny43NTQgMTYuNzA3NEMyOTEuMzExIDI4Ljk0OTIgMjg0LjI3IDQxLjc1NyAyNzIuMDI4IDQ1LjMxMzhMNzEuMTcyNyAxMDMuNjcxQzQwLjcxNDIgMTEyLjUyMSAzNy4xOTc2IDE1NC4yNjIgNjUuNzQ1OSAxNjguMDgzTDI0MS4zNDMgMjUzLjA5M0MzMDcuODcyIDI4NS4zMDIgMjk5Ljc5NCAzODIuNTQ2IDIyOC44NjIgNDAzLjMzNkwzMC40MDQxIDQ2MS41MDJDMTguMTcwNyA0NjUuMDg4IDUuMzQ3MDggNDU4LjA3OCAxLjc2MTUzIDQ0NS44NDRDLTEuODIzOSA0MzMuNjExIDUuMTg2MzcgNDIwLjc4NyAxNy40MTk3IDQxNy4yMDJMMjE1Ljg3OCAzNTkuMDM1QzI0Ni4yNzcgMzUwLjEyNSAyNDkuNzM5IDMwOC40NDkgMjIxLjIyNiAyOTQuNjQ1TDQ1LjYyOTcgMjA5LjYzNUMtMjAuOTgzNCAxNzcuMzg2IC0xMi43NzcyIDc5Ljk4OTMgNTguMjkyOCA1OS4zNDAyTDI1OS4xNDcgMC45ODE4MTJaIiBmaWxsPSIjRkZGRkZGIi8+Cjwvc3ZnPgo=&logoColor=white)](https://github.com/cagataycali/awesome-strands-agents)

[![PyPI version](https://badge.fury.io/py/strands-utcp.svg)](https://badge.fury.io/py/strands-utcp)
[![Python Support](https://img.shields.io/pypi/pyversions/strands-utcp.svg)](https://pypi.org/project/strands-utcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Universal Tool Calling Protocol (UTCP) community plugin for [Strands Agents SDK](https://github.com/strands-agents/sdk-python)

## Features

- **Universal Tool Access** - Connect to any UTCP-compatible tool source
- **OpenAPI/Swagger Support** - Automatic tool discovery from API specifications  
- **Multiple Sources** - Connect to multiple tool sources simultaneously
- **Async/Await Support** - Full async support with context managers
- **Type Safe** - Full type hints and validation
- **Easy Integration** - Drop-in tool adapter for Strands agents

**Key Technical Features:**
- **AgentTool Inheritance**: Full inheritance from Strands `AgentTool` base class
- **Tool Name Sanitization**: UUID suffixes for names >64 characters (Bedrock requirement)

## Requirements

- Python 3.10+
- Strands Agents SDK 1.7.0+
- UTCP core libraries 1.0+

## Installation

```bash
pip install strands-agents strands-utcp
```

## Quick Start

### Basic Usage

```python
from strands import Agent
from strands_utcp import UtcpToolAdapter

# Configure UTCP tool adapter
config = {
    "manual_call_templates": [
        {
            "name": "weather_api",
            "call_template_type": "http",
            "url": "https://api.weather.com/utcp",
            "http_method": "GET"
        }
    ]
}

# Use UTCP tools with Strands agent
async def main():
    async with UtcpToolAdapter(config) as adapter:
        # Get available tools
        tools = adapter.list_tools()
        print(f"Found {len(tools)} UTCP tools")
        
        # Create agent with UTCP tools
        agent = Agent(tools=adapter.to_strands_tools())
        
        # Use the agent
        response = await agent.invoke_async("What's the weather like today?")
        print(response.message)

import asyncio
asyncio.run(main())
```

### Tool Discovery

```python
async with UtcpToolAdapter(config) as adapter:
    # List all available tools
    all_tools = adapter.list_tools()
    
    # Search for specific tools
    weather_tools = await adapter.search_tools("weather")
    
    # Get a specific tool
    weather_tool = adapter.get_tool("get_weather")
    
    if weather_tool:
        result = await weather_tool.call(location="New York")
        print(result)
```

### Multiple Sources

```python
config = {
    "manual_call_templates": [
        {
            "name": "petstore",
            "call_template_type": "http", 
            "url": "https://petstore.swagger.io/v2/swagger.json"
        },
        {
            "name": "openlibrary",
            "call_template_type": "http",
            "url": "https://openlibrary.org/static/openapi.json"
        }
    ]
}

async with UtcpToolAdapter(config) as adapter:
    tools = adapter.list_tools()
    print(f"Total tools from all sources: {len(tools)}")
```

## Configuration

### Supported Call Template Types

The plugin supports all UTCP call template types:

#### HTTP Templates
```python
{
    "name": "api_name",
    "call_template_type": "http",
    "url": "https://api.example.com/utcp",
    "http_method": "GET",  # GET, POST, PUT, DELETE
    "content_type": "application/json"
}
```

#### Server-Sent Events (SSE)
```python
{
    "name": "sse_stream",
    "call_template_type": "sse", 
    "url": "https://api.example.com/stream",
    "http_method": "GET"
}
```

#### Streamable HTTP
```python
{
    "name": "http_stream",
    "call_template_type": "streamable_http",
    "url": "https://api.example.com/stream",
    "http_method": "POST"
}
```

#### Command Line Interface
```python
{
    "name": "cli_tool",
    "call_template_type": "cli",
    "command": "python script.py"
}
```

#### GraphQL
```python
{
    "name": "graphql_api",
    "call_template_type": "graphql",
    "url": "https://api.example.com/graphql"
}
```

#### Model Context Protocol (MCP)
```python
{
    "name": "mcp_server",
    "call_template_type": "mcp",
    "command": "node mcp-server.js"
}
```

#### TCP Socket
```python
{
    "name": "tcp_service",
    "call_template_type": "tcp",
    "host": "localhost",
    "port": 8080
}
```

#### UDP Socket
```python
{
    "name": "udp_service", 
    "call_template_type": "udp",
    "host": "localhost",
    "port": 8081
}
```

#### Text File
```python
{
    "name": "text_tools",
    "call_template_type": "text",
    "file_path": "/path/to/tools.txt"
}
```

## API Reference

### UtcpToolAdapter

Main adapter class for UTCP tool integration.

#### Methods

- `start()` - Initialize the UTCP client
- `stop()` - Clean up resources  
- `list_tools()` - Get all available tools
- `get_tool(name)` - Get specific tool by name
- `search_tools(query, max_results)` - Search for tools
- `call_tool(name, arguments)` - Execute a tool
- `to_strands_tools()` - Convert to Strands tool format

### UtcpAgentTool

Wrapper for individual UTCP tools.

#### Properties

- `name` - Tool name (sanitized)
- `description` - Tool description
- `input_schema` - JSON Schema for inputs

#### Methods

- `call(**kwargs)` - Execute the tool

### UtcpToolAdapterError

Exception raised for UTCP-specific errors.

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=strands_utcp --cov-report=html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [Strands Agents SDK](https://github.com/strands-agents/sdk-python)
- [UTCP Specification](https://github.com/universal-tool-calling-protocol/utcp-specification)
- [UTCP Python Implementation](https://github.com/universal-tool-calling-protocol/python-utcp)
- [PyPI Package](https://pypi.org/project/strands-utcp/)


---

Built for the UTCP and Strands communities 🚀
