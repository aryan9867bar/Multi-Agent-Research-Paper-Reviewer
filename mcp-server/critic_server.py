"""
MCP Server for Critic Agent
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.server_base import SimpleMCPServer
from agents.critic_agent import CriticAgent


class CriticMCPServer(SimpleMCPServer):
    """MCP Server for Critic Agent"""
    
    def __init__(self, port: int = 8003):
        self.agent = CriticAgent()
        super().__init__("critic-server", port)
    
    def register_tools(self):
        """Register Critic agent tools"""
        
        async def validate_review(review_data: dict, original_content: dict) -> dict:
            """Validate and critique a paper review"""
            result = self.agent.process(review_data, original_content)
            return result
        
        async def check_quality(review_data: dict) -> dict:
            """Check the quality of a review"""
            # Simplified version - just validation
            original_content = {'content': ''}  # Would come from context
            result = self.agent.process(review_data, original_content)
            return {
                'validation': result.get('validation', {}),
                'critique': result.get('critique', ''),
                'status': result.get('status', 'error')
            }
        
        self.tools = {
            "validate_review": {
                "description": "Validate and critique a paper review for quality and completeness",
                "function": validate_review,
                "schema": {
                    "type": "object",
                    "properties": {
                        "review_data": {
                            "type": "object",
                            "description": "Review data from Reviewer agent",
                            "properties": {
                                "review": {"type": "object"},
                                "summary": {"type": "string"}
                            }
                        },
                        "original_content": {
                            "type": "object",
                            "description": "Original paper content from Reader agent"
                        }
                    },
                    "required": ["review_data", "original_content"]
                }
            },
            "check_quality": {
                "description": "Check the quality of a review",
                "function": check_quality,
                "schema": {
                    "type": "object",
                    "properties": {
                        "review_data": {
                            "type": "object",
                            "description": "Review data to check"
                        }
                    },
                    "required": ["review_data"]
                }
            }
        }


if __name__ == "__main__":
    # Test server
    server = CriticMCPServer()
    
    # Test request
    test_request = {
        "method": "tools/list"
    }
    response = server.handle_request_sync(test_request)
    print("Tools list:", json.dumps(response, indent=2))

