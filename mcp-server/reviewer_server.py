"""
MCP Server for MetaReviewer Agent
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.server_base import SimpleMCPServer
from agents.meta_reviewer_agent import MetaReviewerAgent


class ReviewerMCPServer(SimpleMCPServer):
    """MCP Server for MetaReviewer Agent"""
    
    def __init__(self, port: int = 8002):
        self.agent = MetaReviewerAgent()
        super().__init__("reviewer-server", port)
    
    def register_tools(self):
        """Register Reviewer agent tools"""
        
        async def review_paper(paper_content: dict) -> dict:
            """Review and summarize a research paper"""
            result = self.agent.process(paper_content)
            return result
        
        async def generate_summary(paper_content: dict) -> dict:
            """Generate student-friendly summary of a paper"""
            result = self.agent.process(paper_content)
            return {
                'summary': result.get('summary', ''),
                'status': result.get('status', 'error')
            }
        
        self.tools = {
            "review_paper": {
                "description": "Review and summarize a research paper in student-friendly language",
                "function": review_paper,
                "schema": {
                    "type": "object",
                    "properties": {
                        "paper_content": {
                            "type": "object",
                            "description": "Paper content from Reader agent",
                            "properties": {
                                "content": {"type": "string"},
                                "structured_info": {"type": "object"},
                                "metadata": {"type": "object"}
                            }
                        }
                    },
                    "required": ["paper_content"]
                }
            },
            "generate_summary": {
                "description": "Generate a concise student-friendly summary",
                "function": generate_summary,
                "schema": {
                    "type": "object",
                    "properties": {
                        "paper_content": {
                            "type": "object",
                            "description": "Paper content from Reader agent"
                        }
                    },
                    "required": ["paper_content"]
                }
            }
        }


if __name__ == "__main__":
    # Test server
    server = ReviewerMCPServer()
    
    # Test request
    test_request = {
        "method": "tools/list"
    }
    response = server.handle_request_sync(test_request)
    print("Tools list:", json.dumps(response, indent=2))

