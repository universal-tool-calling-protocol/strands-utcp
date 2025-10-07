"""Unit tests for UTCP tool provider."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from strands_utcp import UTCPToolProvider, UTCPToolProviderError


@pytest.fixture
def provider_config():
    """Sample provider configuration."""
    return {
        "manual_call_templates": [
            {
                "name": "test_api",
                "call_template_type": "http",
                "url": "https://api.test.com/utcp",
                "http_method": "GET"
            }
        ]
    }


@pytest.fixture
def mock_utcp_tool():
    """Mock UTCP tool."""
    tool = MagicMock()
    tool.name = "test_tool"
    tool.description = "Test tool description"
    tool.inputs.type = "object"
    tool.inputs.properties = {"param1": {"type": "string"}}
    tool.inputs.required = ["param1"]
    tool.inputs.description = "Test input schema"
    return tool


def test_provider_initialization(provider_config):
    """Test UTCPToolProvider initialization."""
    provider = UTCPToolProvider(provider_config)
    assert provider._config == provider_config
    assert provider._utcp_client is None
    assert provider._tools_cache == []


def test_provider_initialization_empty_config():
    """Test UTCPToolProvider initialization with empty config."""
    provider = UTCPToolProvider()
    assert provider._config == {}
    assert provider._utcp_client is None


@pytest.mark.asyncio
async def test_provider_context_manager(provider_config):
    """Test UTCPToolProvider as async context manager."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        async with UTCPToolProvider(provider_config) as provider:
            assert provider._utcp_client is not None
            mock_client_class.create.assert_called_once()
        
        # After context exit, client should be cleaned up
        assert provider._utcp_client is None


@pytest.mark.asyncio
async def test_provider_start_success(provider_config, mock_utcp_tool):
    """Test successful provider start."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        provider = UTCPToolProvider(provider_config)
        result = await provider.start()
        
        assert result is provider
        assert provider._utcp_client is not None
        assert len(provider._tools_cache) == 1
        mock_client_class.create.assert_called_once()


@pytest.mark.asyncio
async def test_provider_start_failure(provider_config):
    """Test provider start failure."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client_class.create.side_effect = Exception("Connection failed")
        
        provider = UTCPToolProvider(provider_config)
        
        with pytest.raises(UTCPToolProviderError, match="UTCP tool provider initialization failed"):
            await provider.start()


@pytest.mark.asyncio
async def test_list_tools(provider_config, mock_utcp_tool):
    """Test listing tools."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UTCPToolProvider(provider_config) as provider:
            tools = provider.list_tools()
            
            assert len(tools) == 1
            assert tools[0].name == "test_tool"
            assert tools[0].description == "Test tool description"


@pytest.mark.asyncio
async def test_get_tool(provider_config, mock_utcp_tool):
    """Test getting specific tool."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UTCPToolProvider(provider_config) as provider:
            tool = provider.get_tool("test_tool")
            assert tool is not None
            assert tool.name == "test_tool"
            
            # Test non-existent tool
            missing_tool = provider.get_tool("missing_tool")
            assert missing_tool is None


@pytest.mark.asyncio
async def test_call_tool(provider_config, mock_utcp_tool):
    """Test calling a tool."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        mock_client.call_tool.return_value = {"result": "success"}
        
        async with UTCPToolProvider(provider_config) as provider:
            result = await provider.call_tool("test_tool", {"param1": "value1"})
            
            assert result == {"result": "success"}
            mock_client.call_tool.assert_called_once_with(
                tool_name="test_tool",
                tool_args={"param1": "value1"}
            )


@pytest.mark.asyncio
async def test_call_tool_not_initialized():
    """Test calling tool when provider not initialized."""
    provider = UTCPToolProvider()
    
    with pytest.raises(UTCPToolProviderError, match="UTCP client not initialized"):
        await provider.call_tool("test_tool", {})


@pytest.mark.asyncio
async def test_search_tools(provider_config, mock_utcp_tool):
    """Test searching tools."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UTCPToolProvider(provider_config) as provider:
            # Initial search_tools call during start() loads tools
            # Now test the search functionality
            mock_client.search_tools.return_value = [mock_utcp_tool]
            
            results = await provider.search_tools("test", max_results=10)
            
            assert len(results) == 1
            assert results[0].name == "test_tool"
            
            # Verify the search was called with correct parameters
            # Note: search_tools is called twice - once during start() and once in our test
            assert mock_client.search_tools.call_count >= 2


@pytest.mark.asyncio
async def test_to_strands_tools(provider_config, mock_utcp_tool):
    """Test converting to Strands tools format."""
    with patch('strands_utcp.utcp_tool_provider.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UTCPToolProvider(provider_config) as provider:
            strands_tools = provider.to_strands_tools()
            
            assert len(strands_tools) == 1
            tool_spec = strands_tools[0]
            
            assert tool_spec.name == "test_tool"


def test_utcp_agent_tool_properties(mock_utcp_tool):
    """Test UTCPAgentTool properties."""
    from strands_utcp.utcp_tool_provider import UTCPAgentTool
    
    provider = MagicMock()
    tool = UTCPAgentTool(mock_utcp_tool, provider)
    
    assert tool.name == "test_tool"
    assert tool.description == "Test tool description"
    
    schema = tool.input_schema
    assert schema["type"] == "object"
    assert schema["properties"] == {"param1": {"type": "string"}}
    assert schema["required"] == ["param1"]
    assert schema["description"] == "Test input schema"


def test_utcp_agent_tool_name_sanitization():
    """Test tool name sanitization."""
    from strands_utcp.utcp_tool_provider import UTCPAgentTool
    
    mock_tool = MagicMock()
    mock_tool.name = "api.v1.get_data"  # Name with dots
    mock_tool.description = "Test tool"
    mock_tool.inputs.type = "object"
    mock_tool.inputs.properties = {}
    mock_tool.inputs.required = []
    mock_tool.inputs.description = None
    
    provider = MagicMock()
    tool = UTCPAgentTool(mock_tool, provider)
    
    # Dots should be replaced with underscores
    assert tool.name == "api_v1_get_data"


@pytest.mark.asyncio
async def test_utcp_agent_tool_call():
    """Test UTCPAgentTool call method."""
    from strands_utcp.utcp_tool_provider import UTCPAgentTool
    
    mock_utcp_tool = MagicMock()
    mock_utcp_tool.name = "test_tool"
    
    mock_provider = AsyncMock()
    mock_provider.call_tool.return_value = {"result": "success"}
    
    tool = UTCPAgentTool(mock_utcp_tool, mock_provider)
    result = await tool.call(param1="value1")
    
    assert result == {"result": "success"}
    mock_provider.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})
