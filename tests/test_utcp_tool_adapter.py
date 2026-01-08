"""Unit tests for UTCP tool adapter."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from strands_utcp import UtcpToolAdapter, UtcpToolAdapterError


@pytest.fixture
def adapter_config():
    """Sample adapter configuration."""
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


def test_adapter_initialization(adapter_config):
    """Test UtcpToolAdapter initialization."""
    adapter = UtcpToolAdapter(adapter_config)
    assert adapter._config == adapter_config
    assert adapter._utcp_client is None
    assert adapter._tools_cache == []


def test_adapter_initialization_empty_config():
    """Test UtcpToolAdapter initialization with empty config."""
    adapter = UtcpToolAdapter()
    assert adapter._config == {}
    assert adapter._utcp_client is None


@pytest.mark.asyncio
async def test_adapter_context_manager(adapter_config):
    """Test UtcpToolAdapter as async context manager."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        async with UtcpToolAdapter(adapter_config) as adapter:
            assert adapter._utcp_client is not None
            mock_client_class.create.assert_called_once()
        
        # After context exit, client should be cleaned up
        assert adapter._utcp_client is None


@pytest.mark.asyncio
async def test_adapter_start_success(adapter_config, mock_utcp_tool):
    """Test successful adapter start."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        adapter = UtcpToolAdapter(adapter_config)
        result = await adapter.start()
        
        assert result is adapter
        assert adapter._utcp_client is not None
        assert len(adapter._tools_cache) == 1
        mock_client_class.create.assert_called_once()


@pytest.mark.asyncio
async def test_adapter_start_failure(adapter_config):
    """Test adapter start failure."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client_class.create.side_effect = Exception("Connection failed")
        
        adapter = UtcpToolAdapter(adapter_config)
        
        with pytest.raises(UtcpToolAdapterError, match="UTCP tool adapter initialization failed"):
            await adapter.start()


@pytest.mark.asyncio
async def test_list_tools(adapter_config, mock_utcp_tool):
    """Test listing tools."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UtcpToolAdapter(adapter_config) as adapter:
            tools = adapter.list_tools()
            
            assert len(tools) == 1
            assert tools[0].name == "test_tool"
            assert tools[0].description == "Test tool description"


@pytest.mark.asyncio
async def test_get_tool(adapter_config, mock_utcp_tool):
    """Test getting specific tool."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UtcpToolAdapter(adapter_config) as adapter:
            tool = adapter.get_tool("test_tool")
            assert tool is not None
            assert tool.name == "test_tool"
            
            # Test non-existent tool
            missing_tool = adapter.get_tool("missing_tool")
            assert missing_tool is None


@pytest.mark.asyncio
async def test_call_tool(adapter_config, mock_utcp_tool):
    """Test calling a tool."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        mock_client.call_tool.return_value = {"result": "success"}
        
        async with UtcpToolAdapter(adapter_config) as adapter:
            result = await adapter.call_tool("test_tool", {"param1": "value1"})
            
            assert result == {"result": "success"}
            mock_client.call_tool.assert_called_once_with(
                tool_name="test_tool",
                tool_args={"param1": "value1"}
            )


@pytest.mark.asyncio
async def test_call_tool_not_initialized():
    """Test calling tool when adapter not initialized."""
    adapter = UtcpToolAdapter()
    
    with pytest.raises(UtcpToolAdapterError, match="UTCP client not initialized"):
        await adapter.call_tool("test_tool", {})


@pytest.mark.asyncio
async def test_search_tools(adapter_config, mock_utcp_tool):
    """Test searching tools."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UtcpToolAdapter(adapter_config) as adapter:
            # Initial search_tools call during start() loads tools
            # Now test the search functionality
            mock_client.search_tools.return_value = [mock_utcp_tool]
            
            results = await adapter.search_tools("test", max_results=10)
            
            assert len(results) == 1
            assert results[0].name == "test_tool"
            
            # Verify the search was called with correct parameters
            # Note: search_tools is called twice - once during start() and once in our test
            assert mock_client.search_tools.call_count >= 2


@pytest.mark.asyncio
async def test_to_strands_tools(adapter_config, mock_utcp_tool):
    """Test converting to Strands tools format."""
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = [mock_utcp_tool]
        
        async with UtcpToolAdapter(adapter_config) as adapter:
            strands_tools = adapter.to_strands_tools()
            
            assert len(strands_tools) == 1
            tool_spec = strands_tools[0]
            
            assert tool_spec.name == "test_tool"


def test_utcp_agent_tool_properties(mock_utcp_tool):
    """Test UtcpAgentTool properties."""
    from strands_utcp.utcp_tool_adapter import UtcpAgentTool
    
    adapter = MagicMock()
    tool = UtcpAgentTool(mock_utcp_tool, adapter)
    
    assert tool.name == "test_tool"
    assert tool.description == "Test tool description"
    
    schema = tool.input_schema
    assert schema["type"] == "object"
    assert schema["properties"] == {"param1": {"type": "string"}}
    assert schema["required"] == ["param1"]
    assert schema["description"] == "Test input schema"


def test_utcp_agent_tool_name_sanitization():
    """Test tool name sanitization."""
    from strands_utcp.utcp_tool_adapter import UtcpAgentTool
    
    mock_tool = MagicMock()
    mock_tool.name = "api.v1.get_data"  # Name with dots
    mock_tool.description = "Test tool"
    mock_tool.inputs.type = "object"
    mock_tool.inputs.properties = {}
    mock_tool.inputs.required = []
    mock_tool.inputs.description = None
    
    adapter = MagicMock()
    tool = UtcpAgentTool(mock_tool, adapter)
    
    # Dots should be replaced with underscores
    assert tool.name == "api_v1_get_data"


@pytest.mark.asyncio
async def test_utcp_agent_tool_call():
    """Test UtcpAgentTool call method."""
    from strands_utcp.utcp_tool_adapter import UtcpAgentTool
    
    mock_utcp_tool = MagicMock()
    mock_utcp_tool.name = "test_tool"
    
    mock_adapter = AsyncMock()
    mock_adapter.call_tool.return_value = {"result": "success"}
    
    tool = UtcpAgentTool(mock_utcp_tool, mock_adapter)
    result = await tool.call(param1="value1")
    
    assert result == {"result": "success"}
    mock_adapter.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})


@pytest.mark.asyncio
async def test_http_call_template_auth_passthrough():
    """Test that auth parameters are passed through to HttpCallTemplate."""
    from strands_utcp.utcp_tool_adapter import HttpCallTemplate
    
    config = {
        "manual_call_templates": [
            {
                "name": "test_api",
                "call_template_type": "http",
                "url": "https://api.test.com/utcp",
                "http_method": "POST",
                "auth": {
                    "auth_type": "api_key",
                    "api_key": "Bearer ${MY_BEARER_TOKEN}",
                    "var_name": "Authorization",
                    "location": "header"
                },
                "auth_tools": ["tool1", "tool2"],
                "headers": {"X-Custom-Header": "value"},
                "body_field": "data",
                "header_fields": ["X-Request-ID"]
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.HttpCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                # Verify HttpCallTemplate was called with all parameters
                mock_template_class.assert_called_once()
                call_kwargs = mock_template_class.call_args[1]
                
                assert call_kwargs["name"] == "test_api"
                assert call_kwargs["call_template_type"] == "http"
                assert call_kwargs["url"] == "https://api.test.com/utcp"
                assert call_kwargs["http_method"] == "POST"
                assert call_kwargs["auth"] == config["manual_call_templates"][0]["auth"]
                assert call_kwargs["auth_tools"] == ["tool1", "tool2"]
                assert call_kwargs["headers"] == {"X-Custom-Header": "value"}
                assert call_kwargs["body_field"] == "data"
                assert call_kwargs["header_fields"] == ["X-Request-ID"]


@pytest.mark.asyncio
async def test_sse_call_template_auth_passthrough():
    """Test that auth and SSE-specific parameters are passed through to SseCallTemplate."""
    from strands_utcp.utcp_tool_adapter import SseCallTemplate
    
    config = {
        "manual_call_templates": [
            {
                "name": "test_sse",
                "call_template_type": "sse",
                "url": "https://api.test.com/sse",
                "http_method": "GET",
                "auth": {
                    "auth_type": "bearer",
                    "token": "${MY_TOKEN}"
                },
                "headers": {"Accept": "text/event-stream"},
                "body_field": "payload",
                "header_fields": ["X-Event-ID"],
                "event_type": "message",
                "reconnect": True,
                "retry_timeout": 5000
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.SseCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                # Verify SseCallTemplate was called with all parameters
                mock_template_class.assert_called_once()
                call_kwargs = mock_template_class.call_args[1]
                
                assert call_kwargs["name"] == "test_sse"
                assert call_kwargs["call_template_type"] == "sse"
                assert call_kwargs["url"] == "https://api.test.com/sse"
                assert call_kwargs["http_method"] == "GET"
                assert call_kwargs["auth"] == config["manual_call_templates"][0]["auth"]
                assert call_kwargs["headers"] == {"Accept": "text/event-stream"}
                assert call_kwargs["body_field"] == "payload"
                assert call_kwargs["header_fields"] == ["X-Event-ID"]
                assert call_kwargs["event_type"] == "message"
                assert call_kwargs["reconnect"] is True
                assert call_kwargs["retry_timeout"] == 5000


@pytest.mark.asyncio
async def test_streamable_http_call_template_auth_passthrough():
    """Test that auth and streamable-specific parameters are passed through to StreamableHttpCallTemplate."""
    from strands_utcp.utcp_tool_adapter import StreamableHttpCallTemplate
    
    config = {
        "manual_call_templates": [
            {
                "name": "test_streamable",
                "call_template_type": "streamable_http",
                "url": "https://api.test.com/stream",
                "http_method": "POST",
                "auth": {
                    "auth_type": "basic",
                    "username": "${MY_USERNAME}",
                    "password": "${MY_PASSWORD}"
                },
                "headers": {"Content-Type": "application/octet-stream"},
                "body_field": "chunk",
                "header_fields": ["X-Chunk-Size"],
                "chunk_size": 8192,
                "timeout": 30.0
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.StreamableHttpCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                # Verify StreamableHttpCallTemplate was called with all parameters
                mock_template_class.assert_called_once()
                call_kwargs = mock_template_class.call_args[1]
                
                assert call_kwargs["name"] == "test_streamable"
                assert call_kwargs["call_template_type"] == "streamable_http"
                assert call_kwargs["url"] == "https://api.test.com/stream"
                assert call_kwargs["http_method"] == "POST"
                assert call_kwargs["auth"] == config["manual_call_templates"][0]["auth"]
                assert call_kwargs["headers"] == {"Content-Type": "application/octet-stream"}
                assert call_kwargs["body_field"] == "chunk"
                assert call_kwargs["header_fields"] == ["X-Chunk-Size"]
                assert call_kwargs["chunk_size"] == 8192
                assert call_kwargs["timeout"] == 30.0


@pytest.mark.asyncio
async def test_http_call_template_optional_params_not_required():
    """Test that HttpCallTemplate works without optional auth/headers parameters."""
    config = {
        "manual_call_templates": [
            {
                "name": "simple_api",
                "call_template_type": "http",
                "url": "https://api.test.com/simple",
                "http_method": "GET"
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.HttpCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                # Verify HttpCallTemplate was called with only required parameters
                mock_template_class.assert_called_once()
                call_kwargs = mock_template_class.call_args[1]
                
                assert call_kwargs["name"] == "simple_api"
                assert call_kwargs["url"] == "https://api.test.com/simple"
                assert call_kwargs["http_method"] == "GET"
                # Optional parameters should not be in kwargs if not provided
                assert "auth" not in call_kwargs
                assert "headers" not in call_kwargs


@pytest.mark.asyncio
async def test_sse_template_minimal_params():
    """Test SseCallTemplate with only required parameters, no SSE-specific fields."""
    config = {
        "manual_call_templates": [
            {
                "name": "minimal_sse",
                "call_template_type": "sse",
                "url": "https://api.test.com/sse"
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.SseCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                call_kwargs = mock_template_class.call_args[1]
                # Verify SSE-specific fields are not present
                assert "event_type" not in call_kwargs
                assert "reconnect" not in call_kwargs
                assert "retry_timeout" not in call_kwargs
                # But common fields are present with defaults
                assert call_kwargs["http_method"] == "GET"
                assert call_kwargs["content_type"] == "application/json"


@pytest.mark.asyncio
async def test_streamable_http_minimal_params():
    """Test StreamableHttpCallTemplate with only required parameters."""
    config = {
        "manual_call_templates": [
            {
                "name": "minimal_stream",
                "call_template_type": "streamable_http",
                "url": "https://api.test.com/stream"
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.StreamableHttpCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                call_kwargs = mock_template_class.call_args[1]
                # Verify streamable-specific fields are not present
                assert "chunk_size" not in call_kwargs
                assert "timeout" not in call_kwargs
                # But common fields are present with defaults
                assert call_kwargs["http_method"] == "GET"
                assert call_kwargs["content_type"] == "application/json"


@pytest.mark.asyncio
async def test_multiple_mixed_templates():
    """Test configuration with multiple template types in one config."""
    config = {
        "manual_call_templates": [
            {
                "name": "api1",
                "call_template_type": "http",
                "url": "http://api1.com"
            },
            {
                "name": "sse1",
                "call_template_type": "sse",
                "url": "http://sse1.com"
            },
            {
                "name": "stream1",
                "call_template_type": "streamable_http",
                "url": "http://stream.com"
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.HttpCallTemplate') as mock_http:
                with patch('strands_utcp.utcp_tool_adapter.SseCallTemplate') as mock_sse:
                    with patch('strands_utcp.utcp_tool_adapter.StreamableHttpCallTemplate') as mock_stream:
                        adapter = UtcpToolAdapter(config)
                        await adapter.start()
                        
                        # Verify each template type was instantiated once
                        mock_http.assert_called_once()
                        mock_sse.assert_called_once()
                        mock_stream.assert_called_once()
                        
                        # Verify the correct URLs were used
                        http_kwargs = mock_http.call_args[1]
                        sse_kwargs = mock_sse.call_args[1]
                        stream_kwargs = mock_stream.call_args[1]
                        
                        assert http_kwargs["name"] == "api1"
                        assert http_kwargs["url"] == "http://api1.com"
                        assert sse_kwargs["name"] == "sse1"
                        assert sse_kwargs["url"] == "http://sse1.com"
                        assert stream_kwargs["name"] == "stream1"
                        assert stream_kwargs["url"] == "http://stream.com"


@pytest.mark.asyncio
async def test_content_type_default():
    """Test that content_type defaults to application/json when not specified."""
    config = {
        "manual_call_templates": [
            {
                "name": "default_content_type",
                "call_template_type": "http",
                "url": "https://api.test.com"
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.HttpCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                call_kwargs = mock_template_class.call_args[1]
                assert call_kwargs["content_type"] == "application/json"


@pytest.mark.asyncio
async def test_content_type_override():
    """Test that content_type can be overridden."""
    config = {
        "manual_call_templates": [
            {
                "name": "custom_content_type",
                "call_template_type": "http",
                "url": "https://api.test.com",
                "content_type": "application/xml"
            }
        ]
    }
    
    with patch('strands_utcp.utcp_tool_adapter.UtcpClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.create = AsyncMock(return_value=mock_client)
        mock_client.search_tools.return_value = []
        
        with patch('strands_utcp.utcp_tool_adapter.UtcpClientConfig') as mock_config_class:
            with patch('strands_utcp.utcp_tool_adapter.HttpCallTemplate') as mock_template_class:
                adapter = UtcpToolAdapter(config)
                await adapter.start()
                
                call_kwargs = mock_template_class.call_args[1]
                assert call_kwargs["content_type"] == "application/xml"
