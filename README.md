# strands-utcp

[![PyPI version](https://badge.fury.io/py/strands-utcp.svg)](https://badge.fury.io/py/strands-utcp)
[![Python Support](https://img.shields.io/pypi/pyversions/strands-utcp.svg)](https://pypi.org/project/strands-utcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Universal Tool Calling Protocol (UTCP) community plugin for [Strands Agents SDK](https://github.com/strands-agents/sdk-python)

## Features

- **Universal Tool Access** - Connect to any UTCP-compatible tool provider
- **OpenAPI/Swagger Support** - Automatic tool discovery from API specifications  
- **Multiple Providers** - Connect to multiple tool sources simultaneously
- **Async/Await Support** - Full async support with context managers
- **Type Safe** - Full type hints and validation
- **Easy Integration** - Drop-in tool provider for Strands agents

## Requirements

- Python 3.10+
- Strands Agents SDK 1.7.0+
- UTCP core libraries

## Installation

```bash
pip install strands-agents strands-utcp
```

## Quick Start

### Basic Usage

```python
from strands import Agent
from strands_utcp import UTCPToolProvider

# Configure UTCP tool provider
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
    async with UTCPToolProvider(config) as provider:
        # Get available tools
        tools = provider.list_tools()
        print(f"Found {len(tools)} UTCP tools")
        
        # Create agent with UTCP tools
        agent = Agent(tools=provider.to_strands_tools())
        
        # Use the agent
        response = await agent.invoke_async("What's the weather like today?")
        print(response.message)

import asyncio
asyncio.run(main())
```

### Tool Discovery

```python
async with UTCPToolProvider(config) as provider:
    # List all available tools
    all_tools = provider.list_tools()
    
    # Search for specific tools
    weather_tools = await provider.search_tools("weather")
    
    # Get a specific tool
    weather_tool = provider.get_tool("get_weather")
    
    if weather_tool:
        result = await weather_tool.call(location="New York")
        print(result)
```

### Multiple Providers

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

async with UTCPToolProvider(config) as provider:
    tools = provider.list_tools()
    print(f"Total tools from all providers: {len(tools)}")
```

## Configuration

### HTTP Call Templates

```python
config = {
    "manual_call_templates": [
        {
            "name": "api_name",
            "call_template_type": "http",
            "url": "https://api.example.com/utcp",
            "http_method": "GET",  # GET, POST, PUT, DELETE
            "content_type": "application/json"
        }
    ]
}
```

### Environment Variables

```bash
# Optional: Set UTCP-specific environment variables
export UTCP_LOG_LEVEL=DEBUG
export UTCP_TIMEOUT=30
```

## Examples

### Weather Agent

```python
from strands import Agent
from strands_utcp import UTCPToolProvider

async def weather_agent():
    config = {
        "manual_call_templates": [{
            "name": "weather_service",
            "call_template_type": "http",
            "url": "https://weather-api.example.com/utcp"
        }]
    }
    
    async with UTCPToolProvider(config) as provider:
        agent = Agent(
            tools=provider.to_strands_tools(),
            system_prompt="You are a helpful weather assistant."
        )
        
        response = await agent.invoke_async(
            "What's the weather forecast for San Francisco this week?"
        )
        return response.message
```

### Multi-Tool Agent

```python
async def multi_tool_agent():
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
    
    async with UTCPToolProvider(config) as provider:
        tools = provider.list_tools()
        print(f"Available tools: {[t.tool_name for t in tools]}")
        
        agent = Agent(tools=provider.to_strands_tools())
        
        response = await agent.invoke_async(
            "Find books about pets and check pet store inventory"
        )
        return response.message
```

## API Reference

### UTCPToolProvider

Main provider class for UTCP tool integration.

#### Methods

- `start()` - Initialize the UTCP client
- `stop()` - Clean up resources  
- `list_tools()` - Get all available tools
- `get_tool(name)` - Get specific tool by name
- `search_tools(query, max_results)` - Search for tools
- `call_tool(name, arguments)` - Execute a tool
- `to_strands_tools()` - Convert to Strands tool format

### UTCPAgentTool

Wrapper for individual UTCP tools.

#### Properties

- `name` - Tool name (sanitized)
- `description` - Tool description
- `input_schema` - JSON Schema for inputs

#### Methods

- `call(**kwargs)` - Execute the tool

### UTCPToolProviderError

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

## Status

- ✅ Basic UTCP integration
- ✅ HTTP call template support  
- ✅ Tool discovery and search
- ✅ Async/await support
- ✅ Multiple provider support
- ✅ End-to-end validation with real APIs
- ✅ Bedrock-compatible tool naming
- ✅ JSON Schema conversion
- 🔄 Advanced authentication (In Progress)
- 🔄 WebSocket support (Planned)
- 🔄 Tool caching (Planned)

## Architecture Analysis

### Plugin Architecture

**Core Components**

1. **UTCPToolProvider**: Main provider class that manages UTCP client lifecycle
2. **UTCPAgentTool**: Wrapper class that adapts UTCP tools for Strands agents
3. **Configuration**: Simple dictionary-based configuration for HTTP call templates

**Implementation Approach**
Following minimal code principles, the plugin focuses on:

- **Essential functionality only**: Tool discovery, execution, and Strands integration
- **No unnecessary abstractions**: Direct mapping between UTCP and Strands concepts
- **Lean dependencies**: Only required packages in pyproject.toml
- **Simple configuration**: Dictionary-based config without complex validation

## Validation Results

The plugin has been extensively validated with real APIs:

- ✅ **31 tools discovered** from OpenAPI specs (Petstore + OpenLibrary)
- ✅ **Real tool execution** with live OpenLibrary API calls
- ✅ **Successful queries** (e.g., William Shakespeare's author ID: OL9388A)
- ✅ **Proper error handling** for unavailable APIs
- ✅ **Bedrock compatibility** with tool name sanitization
- ✅ **JSON Schema validation** with type conversion

## Technical Details

**UTCP Versions Used:**
- UTCP core: 1.0.4
- UTCP-HTTP: 1.0.5

**Key Technical Features:**
- **Tool Name Sanitization**: UUID suffixes for names >64 characters (Bedrock requirement)
- **Schema Conversion**: Handles `type: null` and `JsonSchema` object conversion  
- **AgentTool Inheritance**: Full inheritance from Strands `AgentTool` base class
- **Type Mapping**: Maps invalid types like `"file"` to valid JSON Schema types

---

Built for the UTCP and Strands communities 🚀
