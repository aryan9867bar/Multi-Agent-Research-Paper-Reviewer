"""
MCP Client for interacting with agent servers
"""
import requests
import json
from typing import Dict, Any, Optional


class MCPClient:
    """Client for interacting with MCP servers"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.servers = {
            'reader': f"{base_url}:8001",
            'reviewer': f"{base_url}:8002",
            'critic': f"{base_url}:8003"
        }
    
    def list_tools(self, server_name: str) -> Dict[str, Any]:
        """List available tools on a server"""
        url = self.servers.get(server_name)
        if not url:
            return {"error": f"Unknown server: {server_name}"}
        
        request = {
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = requests.post(url, json=request, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a server"""
        url = self.servers.get(server_name)
        if not url:
            return {"error": f"Unknown server: {server_name}"}
        
        request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = requests.post(url, json=request, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def review_paper(self, paper_id: str, input_type: str = "arxiv_id") -> Dict[str, Any]:
        """Complete paper review workflow using MCP servers"""
        result = {
            'input': paper_id,
            'input_type': input_type,
            'reader': {},
            'reviewer': {},
            'critic': {},
            'success': False
        }
        
        # Step 1: Reader
        try:
            reader_result = self.call_tool('reader', 'read_paper', {input_type: paper_id})
            result['reader'] = reader_result
            if 'error' in reader_result:
                return result
        except Exception as e:
            result['reader'] = {'error': str(e)}
            return result
        
        # Step 2: Reviewer
        try:
            paper_content = reader_result.get('content', [{}])[0] if isinstance(reader_result.get('content'), list) else {}
            if isinstance(paper_content, dict) and 'text' in paper_content:
                # Parse JSON from text
                import json
                paper_data = json.loads(paper_content['text'])
            else:
                paper_data = paper_content
            
            reviewer_result = self.call_tool('reviewer', 'review_paper', {'paper_content': paper_data})
            result['reviewer'] = reviewer_result
            if 'error' in reviewer_result:
                return result
        except Exception as e:
            result['reviewer'] = {'error': str(e)}
            return result
        
        # Step 3: Critic
        try:
            review_data = reviewer_result.get('content', [{}])[0] if isinstance(reviewer_result.get('content'), list) else {}
            if isinstance(review_data, dict) and 'text' in review_data:
                review_data = json.loads(review_data['text'])
            
            critic_result = self.call_tool('critic', 'validate_review', {
                'review_data': review_data,
                'original_content': paper_data
            })
            result['critic'] = critic_result
        except Exception as e:
            result['critic'] = {'error': str(e)}
        
        result['success'] = 'error' not in result['reader'] and 'error' not in result['reviewer']
        return result


if __name__ == "__main__":
    # Test client
    client = MCPClient()
    
    # List tools
    print("Reader tools:", json.dumps(client.list_tools('reader'), indent=2))
    print("\nReviewer tools:", json.dumps(client.list_tools('reviewer'), indent=2))
    print("\nCritic tools:", json.dumps(client.list_tools('critic'), indent=2))

