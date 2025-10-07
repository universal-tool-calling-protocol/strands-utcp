"""Universal Tool Calling Protocol (UTCP) integration for Strands Agents SDK.

This package provides seamless integration between UTCP tool providers and the Strands
Agents framework, enabling agents to discover and use external tools via the UTCP protocol.
"""

from typing import Dict, List, Optional

from .utcp_tool_provider import UTCPToolProvider, UTCPToolProviderError

__version__ = "0.1.0"
__all__ = ["UTCPToolProvider", "UTCPToolProviderError"]


def create_utcp_provider(config: Optional[Dict] = None, **kwargs) -> UTCPToolProvider:
    """Create a UTCP tool provider with default settings.

    Args:
        config: UTCP configuration dictionary
        **kwargs: Additional provider parameters

    Returns:
        Configured UTCPToolProvider instance
    """
    return UTCPToolProvider(config=config, **kwargs)
