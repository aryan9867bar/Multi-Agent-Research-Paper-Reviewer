"""
MCP Server for Reader Agent
"""
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.server_base import SimpleMCPServer
from agents.reader_agent import ReaderAgent


class ReaderMCPServer(SimpleMCPServer):
    """MCP Server for Reader Agent"""
    
    def __init__(self, port: int = 8001):
        self.agent = ReaderAgent()
        super().__init__("reader-server", port)
    
    def register_tools(self):
        """Register Reader agent tools"""
        
        async def read_paper(arxiv_id: str = None, pdf_path: str = None, url: str = None) -> dict:
            """Read a research paper from Arxiv ID, PDF path, or URL"""
            if arxiv_id:
                input_data = {'type': 'arxiv_id', 'value': arxiv_id, 'extract_full_text': True}
            elif pdf_path:
                input_data = {'type': 'pdf_path', 'value': pdf_path}
            elif url:
                input_data = {'type': 'url', 'value': url}
            else:
                return {'error': 'Must provide arxiv_id, pdf_path, or url'}
            
            result = self.agent.process(input_data)
            return result
        
        async def search_papers(query: str, max_results: int = 5) -> dict:
            """Search for papers on Arxiv"""
            from agents.tools import arxiv_api
            results = arxiv_api.search_papers(query, max_results)
            return {'results': results}
        
        self.tools = {
            "read_paper": {
                "description": "Read and extract content from a research paper (Arxiv ID, PDF path, or URL)",
                "function": read_paper,
                "schema": {
                    "type": "object",
                    "properties": {
                        "arxiv_id": {"type": "string", "description": "Arxiv paper ID"},
                        "pdf_path": {"type": "string", "description": "Path to local PDF file"},
                        "url": {"type": "string", "description": "URL to paper"}
                    }
                }
            },
            "search_papers": {
                "description": "Search for papers on Arxiv",
                "function": search_papers,
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        }


if __name__ == "__main__":
    # Test server
    server = ReaderMCPServer()
    
    # Test request
    test_request = {
        "method": "tools/list"
    }
    response = server.handle_request_sync(test_request)
    print("Tools list:", json.dumps(response, indent=2))
    
    # Test tool call
    test_request = {
        "method": "tools/call",
        "params": {
            "name": "read_paper",
            "arguments": {
                "arxiv_id": "1706.03762"
            }
        }
    }
    response = server.handle_request_sync(test_request)
    print("\nTool call result:", json.dumps(response, indent=2)[:500])

