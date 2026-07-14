"""
Base MCP Server Implementation
"""
import json
import asyncio
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class MCPServerBase(ABC):
    """Base class for MCP servers"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.tools = {}
        self.register_tools()
    
    @abstractmethod
    def register_tools(self):
        """Register available tools"""
        pass
    
    @abstractmethod
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        pass
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": name,
                    "description": info.get("description", ""),
                    "inputSchema": info.get("schema", {})
                }
                for name, info in self.tools.items()
            ]
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a registered tool"""
        if tool_name not in self.tools:
            return {
                "error": f"Tool {tool_name} not found",
                "content": []
            }
        
        tool_func = self.tools[tool_name]["function"]
        try:
            result = await tool_func(**arguments)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "content": []
            }


class SimpleMCPServer(MCPServerBase):
    """Simple synchronous MCP server (for testing)"""
    
    def __init__(self, server_name: str, port: int = 8000):
        super().__init__(server_name)
        self.port = port
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "tools/list":
            return self.list_tools()
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            return await self.call_tool(tool_name, arguments)
        else:
            return {
                "error": f"Unknown method: {method}",
                "content": []
            }
    
    def handle_request_sync(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version for testing"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.handle_request(request))
        finally:
            loop.close()

