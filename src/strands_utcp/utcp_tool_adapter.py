"""UTCP Tool Adapter for Strands Agents SDK."""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

from utcp.data.tool import Tool as UTCPTool
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp.utcp_client import UtcpClient

# Import all available call templates
from utcp_http.http_call_template import HttpCallTemplate
from utcp_http.sse_call_template import SseCallTemplate
from utcp_http.streamable_http_call_template import StreamableHttpCallTemplate

# Optional imports for other protocols
try:
    from utcp_cli.cli_call_template import CliCallTemplate
except ImportError:
    CliCallTemplate = None

try:
    from utcp_gql.gql_call_template import GqlCallTemplate
except ImportError:
    GqlCallTemplate = None

try:
    from utcp_mcp.mcp_call_template import McpCallTemplate
except ImportError:
    McpCallTemplate = None

try:
    from utcp_socket.tcp_call_template import TcpCallTemplate
    from utcp_socket.udp_call_template import UdpCallTemplate
except ImportError:
    TcpCallTemplate = None
    UdpCallTemplate = None

try:
    from utcp_text.text_call_template import TextCallTemplate
except ImportError:
    TextCallTemplate = None

# Import Strands types for proper integration
try:
    from strands.types.tools import AgentTool, ToolSpec, ToolUse, ToolGenerator
    from strands.types._events import ToolResultEvent
    from strands.types.tools import ToolResult
except ImportError:
    # Fallback for testing without full Strands installation
    AgentTool = object
    ToolSpec = Dict[str, Any]
    ToolUse = Dict[str, Any] 
    ToolGenerator = Any
    ToolResultEvent = Any
    ToolResult = Dict[str, Any]

logger = logging.getLogger(__name__)


def format_tool_name_for_bedrock(tool_name: str) -> str:
    """Format a tool name to meet Bedrock's requirements.
    
    Bedrock requires tool names to:
    - Be 64 characters or less
    - Match pattern ^[a-zA-Z0-9_-]{1,64}$
    """
    # Replace periods with underscores (common in UTCP tool names)
    bedrock_name = tool_name.replace(".", "_")
    
    # Remove any other invalid characters and replace with underscores
    valid_chars = []
    for char in bedrock_name:
        if char.isalnum() or char in ['_', '-']:
            valid_chars.append(char)
        else:
            valid_chars.append('_')
    
    bedrock_name = ''.join(valid_chars)
    
    # Truncate if longer than 64 characters
    if len(bedrock_name) > 64:
        # Use first 55 chars + underscore + 8-char UUID
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]
        bedrock_name = f"{bedrock_name[:55]}_{short_uuid}"
    
    return bedrock_name


class UtcpToolAdapterError(Exception):
    """Exception for UTCP tool adapter errors."""
    pass


class UtcpAgentTool(AgentTool):
    """Wrapper for UTCP tools to be used with Strands agents."""
    
    def __init__(self, utcp_tool: UTCPTool, adapter: "UtcpToolAdapter"):
        super().__init__()
        self.utcp_tool = utcp_tool
        self.adapter = adapter
        
    @property
    def name(self) -> str:
        """Tool name, sanitized for Bedrock compatibility."""
        return format_tool_name_for_bedrock(self.utcp_tool.name)
    
    @property
    def tool_name(self) -> str:
        """Tool name, sanitized for Bedrock compatibility."""
        return self.name
    
    def _convert_schema_to_dict(self, schema_obj) -> Dict[str, Any]:
        """Convert UTCP JsonSchema object to plain dictionary."""
        if hasattr(schema_obj, 'type'):
            # Map invalid JSON Schema types to valid ones
            type_mapping = {
                "file": "string",  # Files are represented as strings in JSON Schema
                None: "string"     # Default fallback
            }
            schema_type = type_mapping.get(schema_obj.type, schema_obj.type)
            
            result = {"type": schema_type}
            if hasattr(schema_obj, 'description') and schema_obj.description:
                result["description"] = schema_obj.description
            if hasattr(schema_obj, 'enum') and schema_obj.enum:
                result["enum"] = schema_obj.enum
            if hasattr(schema_obj, 'format') and schema_obj.format:
                result["format"] = schema_obj.format
            return result
        return {"type": "string"}  # fallback
    
    @property
    def tool_spec(self) -> ToolSpec:
        """Tool specification in Strands format."""
        # Convert properties to plain dictionaries
        properties = {}
        if self.utcp_tool.inputs.properties:
            for key, value in self.utcp_tool.inputs.properties.items():
                properties[key] = self._convert_schema_to_dict(value)
        
        schema = {
            "type": "object",  # Always object for tool inputs
            "properties": properties,
        }
        
        if self.utcp_tool.inputs.required:
            schema["required"] = self.utcp_tool.inputs.required
        if self.utcp_tool.inputs.description:
            schema["description"] = self.utcp_tool.inputs.description
            
        return {
            "inputSchema": {"json": schema},
            "name": self.tool_name,
            "description": self.description,
        }
    
    @property
    def tool_type(self) -> str:
        """Tool type for Strands."""
        return "utcp"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return self.utcp_tool.description or f"Tool: {self.utcp_tool.name}"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Tool input schema in JSON Schema format."""
        # Convert properties to plain dictionaries
        properties = {}
        if self.utcp_tool.inputs.properties:
            for key, value in self.utcp_tool.inputs.properties.items():
                properties[key] = self._convert_schema_to_dict(value)
        
        schema = {
            "type": "object",  # Always object for tool inputs
            "properties": properties,
        }
        
        if self.utcp_tool.inputs.required:
            schema["required"] = self.utcp_tool.inputs.required
        if self.utcp_tool.inputs.description:
            schema["description"] = self.utcp_tool.inputs.description
            
        return schema
    
    def stream(self, tool_use: ToolUse, invocation_state: Dict[str, Any], **kwargs: Any) -> ToolGenerator:
        """Stream tool execution for Strands."""
        async def _execute():
            try:
                result = await self.adapter.call_tool(
                    self.utcp_tool.name, 
                    tool_use.get("input", {})
                )
                
                # Format result as ToolResult
                if isinstance(result, str):
                    content = result
                elif isinstance(result, dict):
                    content = json.dumps(result, indent=2)
                else:
                    content = str(result)
                
                tool_result = {
                    "toolUseId": tool_use.get("toolUseId", "unknown"),
                    "content": [{"text": content}],
                    "status": "success"
                }
                
                yield ToolResultEvent(tool_result)
                
            except Exception as e:
                error_result = {
                    "toolUseId": tool_use.get("toolUseId", "unknown"),
                    "content": [{"text": f"Error: {str(e)}"}],
                    "status": "error"
                }
                yield ToolResultEvent(error_result)
        
        return _execute()
    
    async def call(self, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        return await self.adapter.call_tool(self.utcp_tool.name, kwargs)


class UtcpToolAdapter:
    """UTCP Tool Adapter for Strands Agents SDK."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize UTCP tool adapter.

        Args:
            config: Configuration dictionary containing:
                   - 'manual_call_templates': List of call template configurations
                     Supported types: http, sse, streamable_http, cli, graphql, mcp, tcp, udp, text
        """
        self._config = config or {}
        self._utcp_client: Optional[UtcpClient] = None
        self._tools_cache: List[UtcpAgentTool] = []
        logger.debug("Initializing UTCP tool adapter with config: %s", config)

    async def __aenter__(self) -> "UtcpToolAdapter":
        """Async context manager entry."""
        return await self.start()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()

    def _build_http_base_kwargs(self, template_config: Dict[str, Any], call_template_type: str) -> Dict[str, Any]:
        """Build base kwargs common to all HTTP-based call templates (http, sse, streamable_http)."""
        kwargs = {
            "name": template_config["name"],
            "call_template_type": call_template_type,
            "url": template_config["url"],
            "http_method": template_config.get("http_method", "GET"),
            "content_type": template_config.get("content_type", "application/json"),
        }
        
        # Add common optional fields
        for field in ["auth", "headers", "body_field", "header_fields"]:
            if field in template_config:
                kwargs[field] = template_config[field]
        
        return kwargs

    async def start(self) -> "UtcpToolAdapter":
        """Initialize and start the UTCP client."""
        try:
            # Convert manual call templates
            call_templates = []
            for template_config in self._config.get("manual_call_templates", []):
                call_template_type = template_config.get("call_template_type")
                
                if call_template_type == "http":
                    http_kwargs = self._build_http_base_kwargs(template_config, "http")
                    if "auth_tools" in template_config:
                        http_kwargs["auth_tools"] = template_config["auth_tools"]
                    
                    call_template = HttpCallTemplate(**http_kwargs)
                    call_templates.append(call_template)
                
                elif call_template_type == "sse":
                    sse_kwargs = self._build_http_base_kwargs(template_config, "sse")
                    for field in ["event_type", "reconnect", "retry_timeout"]:
                        if field in template_config:
                            sse_kwargs[field] = template_config[field]
                    
                    call_template = SseCallTemplate(**sse_kwargs)
                    call_templates.append(call_template)
                
                elif call_template_type == "streamable_http":
                    streamable_kwargs = self._build_http_base_kwargs(template_config, "streamable_http")
                    for field in ["chunk_size", "timeout"]:
                        if field in template_config:
                            streamable_kwargs[field] = template_config[field]
                    
                    call_template = StreamableHttpCallTemplate(**streamable_kwargs)
                    call_templates.append(call_template)
                
                elif call_template_type == "cli" and CliCallTemplate:
                    call_template = CliCallTemplate(
                        name=template_config["name"],
                        call_template_type="cli",
                        command=template_config["command"],
                    )
                    call_templates.append(call_template)
                
                elif call_template_type == "graphql" and GqlCallTemplate:
                    call_template = GqlCallTemplate(
                        name=template_config["name"],
                        call_template_type="graphql",
                        url=template_config["url"],
                    )
                    call_templates.append(call_template)
                
                elif call_template_type == "mcp" and McpCallTemplate:
                    call_template = McpCallTemplate(
                        name=template_config["name"],
                        call_template_type="mcp",
                        command=template_config["command"],
                    )
                    call_templates.append(call_template)
                
                elif call_template_type == "tcp" and TcpCallTemplate:
                    call_template = TcpCallTemplate(
                        name=template_config["name"],
                        call_template_type="tcp",
                        host=template_config["host"],
                        port=template_config["port"],
                    )
                    call_templates.append(call_template)
                
                elif call_template_type == "udp" and UdpCallTemplate:
                    call_template = UdpCallTemplate(
                        name=template_config["name"],
                        call_template_type="udp",
                        host=template_config["host"],
                        port=template_config["port"],
                    )
                    call_templates.append(call_template)
                
                elif call_template_type == "text" and TextCallTemplate:
                    call_template = TextCallTemplate(
                        name=template_config["name"],
                        call_template_type="text",
                        file_path=template_config["file_path"],
                    )
                    call_templates.append(call_template)
                
                else:
                    logger.warning("Unsupported or unavailable call template type: %s", call_template_type)

            # Create UTCP client config
            utcp_config = UtcpClientConfig(manual_call_templates=call_templates)
            
            # Initialize UTCP client
            self._utcp_client = await UtcpClient.create(config=utcp_config)
            
            # Load tools
            await self._load_tools()
            
            logger.info("UTCP tool adapter started successfully with %d tools", len(self._tools_cache))
            return self

        except Exception as e:
            logger.error("Failed to start UTCP tool adapter: %s", e)
            raise UtcpToolAdapterError(f"UTCP tool adapter initialization failed: {e}") from e

    async def stop(self) -> None:
        """Stop and cleanup the UTCP client."""
        if self._utcp_client:
            self._utcp_client = None
            self._tools_cache.clear()
            logger.info("UTCP tool adapter stopped")

    async def _load_tools(self) -> None:
        """Load tools from UTCP client."""
        if not self._utcp_client:
            return
            
        try:
            utcp_tools = await self._utcp_client.search_tools(query="", limit=1000)
            self._tools_cache = [UtcpAgentTool(tool, self) for tool in utcp_tools]
            logger.debug("Loaded %d tools from UTCP client", len(self._tools_cache))
        except Exception as e:
            logger.error("Failed to load tools: %s", e)
            self._tools_cache = []

    def list_tools(self) -> List[UtcpAgentTool]:
        """Get list of available tools."""
        return self._tools_cache.copy()

    def get_tool(self, name: str) -> Optional[UtcpAgentTool]:
        """Get a specific tool by name."""
        for tool in self._tools_cache:
            if tool.tool_name == name or tool.utcp_tool.name == name:
                return tool
        return None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments."""
        if not self._utcp_client:
            raise UtcpToolAdapterError("UTCP client not initialized")

        try:
            logger.debug("Calling tool %s with arguments: %s", tool_name, arguments)
            result = await self._utcp_client.call_tool(tool_name=tool_name, tool_args=arguments)
            logger.debug("Tool %s returned: %s", tool_name, result)
            return result
        except Exception as e:
            logger.error("Failed to call tool %s: %s", tool_name, e)
            raise UtcpToolAdapterError(f"Tool execution failed: {e}") from e

    async def search_tools(self, query: str, max_results: Optional[int] = None) -> List[UtcpAgentTool]:
        """Search for tools matching the query."""
        if not self._utcp_client:
            raise UtcpToolAdapterError("UTCP client not initialized")

        try:
            limit = max_results or 100
            utcp_tools = await self._utcp_client.search_tools(query=query, limit=limit)
            return [UtcpAgentTool(tool, self) for tool in utcp_tools]
        except Exception as e:
            logger.error("Failed to search tools: %s", e)
            return []

    def to_strands_tools(self) -> List[UtcpAgentTool]:
        """Convert UTCP tools to Strands-compatible tool objects."""
        return self._tools_cache.copy()
