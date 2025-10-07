"""Universal Tool Calling Protocol (UTCP) integration for Strands Agents SDK.

This package provides seamless integration between UTCP tool providers and the Strands
Agents framework, enabling agents to discover and use external tools via the UTCP protocol.
"""

from typing import Dict, List, Optional

from .utcp_tool_adapter import UtcpToolAdapter, UtcpToolAdapterError

__version__ = "0.1.0"
__all__ = ["UtcpToolAdapter", "UtcpToolAdapterError"]


def create_utcp_adapter(config: Optional[Dict] = None, **kwargs) -> UtcpToolAdapter:
    """Create a UTCP tool provider with default settings.

    Args:
        config: UTCP configuration dictionary
        **kwargs: Additional adapter parameters

    Returns:
        Configured UtcpToolAdapter instance
    """
    return UtcpToolAdapter(config=config, **kwargs)
