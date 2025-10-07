#!/usr/bin/env python
"""Basic usage example of strands-utcp."""

import asyncio
import os
from dotenv import load_dotenv

from strands_utcp import UtcpToolAdapter
from strands import Agent


async def main():
    """Run basic UTCP example."""
    # Load environment variables
    load_dotenv()
    
    print("=== Basic UTCP Tool Provider Example ===\n")
    
    # Configure UTCP tool provider with real OpenAPI endpoints
    config = {
        "manual_call_templates": [
            {
                "name": "petstore",
                "call_template_type": "http",
                "http_method": "GET",
                "url": "https://petstore.swagger.io/v2/swagger.json"
            },
            {
                "name": "openlibrary", 
                "call_template_type": "http",
                "http_method": "GET",
                "url": "https://openlibrary.org/static/openapi.json"
            }
        ]
    }
    
    # Use UTCP tool provider
    async with UtcpToolAdapter(config) as adapter:
        print("UTCP tool provider initialized successfully")
        
        # List available tools
        tools = adapter.list_tools()
        print(f"Found {len(tools)} UTCP tools:")
        
        for tool in tools:
            print(f"  - {tool.tool_name}: {tool.description}")
        
        # Search for specific tools
        pet_tools = await adapter.search_tools("pet", max_results=5)
        print(f"\nFound {len(pet_tools)} pet-related tools:")
        
        for tool in pet_tools:
            print(f"  - {tool.tool_name}: {tool.description}")
        
        # Search for OpenLibrary tools specifically
        openlibrary_tools = [tool for tool in tools if "openlibrary" in tool.tool_name][:5]
        print(f"\nFound {len(openlibrary_tools)} OpenLibrary tools:")
        
        for tool in openlibrary_tools:
            print(f"  - {tool.tool_name}: {tool.description}")
        
        # Create agent with UTCP tools
        if tools:
            print(f"\nCreating agent with {len(tools)} UTCP tools...")
            agent = Agent(
                tools=adapter.to_strands_tools(),
                system_prompt="You are a helpful assistant with access to external tools."
            )
            
            # Example conversation
            print("\nAgent: Ready to help! I have access to external tools via UTCP.")
            print("You can ask me to use pet store APIs, library services, or other tools.")
            
            # Example tool usage - Shakespeare author lookup
            print("\nExample: Find Shakespeare's author ID in OpenLibrary")
            try:
                response = await agent.invoke_async("Can you find William Shakespeare's author ID in the OpenLibrary database?")
                print(f"Agent: {response.message}")
            except Exception as e:
                print(f"Error: {e}")
            
            # Example tool usage - Pet store
            if pet_tools:
                print("\nExample: Find information about pets in the store")
                try:
                    response = await agent.invoke_async("What pets are available in the store?")
                    print(f"Agent: {response.message}")
                except Exception as e:
                    print(f"Tool execution error: {e}")
        else:
            print("\nNo tools available - check API endpoints")


if __name__ == "__main__":
    asyncio.run(main())
