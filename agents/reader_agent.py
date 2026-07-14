"""
Reader Agent: Reads and extracts content from research papers
"""
from typing import Dict, List, Optional
from agents.tools import file_io, arxiv_api, pdf_extractor, web_crawler
from agents.llm_client import get_default_llm


class ReaderAgent:
    """Agent responsible for reading and extracting paper content"""
    
    def __init__(self, llm=None):
        self.llm = llm or get_default_llm()
        self.name = "Reader"
        self.role = "Read and extract key information from research papers"
    
    def process(self, input_data: Dict) -> Dict:
        """
        Process input: can be paper ID, PDF path, or URL
        
        Args:
            input_data: Dict with 'type' and 'value'
                - type: 'arxiv_id', 'pdf_path', or 'url'
                - value: corresponding value
        
        Returns:
            Dict with extracted content and metadata
        """
        input_type = input_data.get('type', '')
        input_value = input_data.get('value', '')
        
        result = {
            'agent': self.name,
            'status': 'success',
            'content': '',
            'metadata': {}
        }
        
        try:
            if input_type == 'arxiv_id':
                # Fetch from Arxiv
                paper_info = arxiv_api.get_paper_by_id(input_value)
                if paper_info and 'error' not in paper_info:
                    result['content'] = f"Title: {paper_info['title']}\n\n"
                    result['content'] += f"Authors: {', '.join(paper_info['authors'])}\n\n"
                    result['content'] += f"Abstract: {paper_info['summary']}\n\n"
                    result['metadata'] = {
                        'paper_id': paper_info['id'],
                        'title': paper_info['title'],
                        'authors': paper_info['authors'],
                        'published': paper_info['published'],
                        'categories': paper_info['categories'],
                        'pdf_url': paper_info['pdf_url']
                    }
                    
                    # Optionally download and extract full text
                    if input_data.get('extract_full_text', False):
                        pdf_path = f"./data/papers/{paper_info['id'].split('/')[-1]}.pdf"
                        if arxiv_api.download_pdf(paper_info['pdf_url'], pdf_path):
                            full_text = pdf_extractor.extract_text(pdf_path)
                            result['content'] += f"\n\nFull Text (excerpt):\n{full_text[:2000]}..."
                else:
                    result['status'] = 'error'
                    result['content'] = f"Error fetching paper: {paper_info.get('error', 'Unknown error')}"
            
            elif input_type == 'pdf_path':
                # Extract from local PDF
                text = pdf_extractor.extract_text(input_value)
                metadata = pdf_extractor.extract_metadata(input_value)
                
                result['content'] = text
                result['metadata'] = metadata
            
            elif input_type == 'url':
                # Fetch from URL
                content = web_crawler.fetch_url(input_value)
                result['content'] = content
                result['metadata'] = {'url': input_value}
            
            else:
                result['status'] = 'error'
                result['content'] = f"Unknown input type: {input_type}"
            
            # Use LLM to extract structured information
            if result['status'] == 'success' and result['content']:
                structured_info = self._extract_structured_info(result['content'])
                result['structured_info'] = structured_info
            
        except Exception as e:
            result['status'] = 'error'
            result['content'] = f"Error in ReaderAgent: {str(e)}"
        
        return result
    
    def _extract_structured_info(self, content: str) -> Dict:
        """Use LLM to extract structured information from paper content"""
        prompt = f"""Extract key information from this research paper content:

{content[:3000]}

Please extract and return a JSON object with:
- main_topic: Main research topic
- key_contributions: List of key contributions
- methodology: Brief description of methodology
- results: Key results or findings
- keywords: List of important keywords

Return only valid JSON, no additional text."""

        system_prompt = "You are an expert at analyzing research papers. Extract structured information accurately."
        
        response = self.llm.generate(prompt, system_prompt, temperature=0.3)
        
        # Try to parse JSON from response
        try:
            import json
            # Extract JSON from response if wrapped in text
            if '{' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        return {'raw_response': response}


if __name__ == "__main__":
    # Test Reader Agent
    agent = ReaderAgent()
    
    # Test with Arxiv ID
    test_input = {
        'type': 'arxiv_id',
        'value': '1706.03762',  # Attention is All You Need
        'extract_full_text': False
    }
    
    result = agent.process(test_input)
    print(f"Status: {result['status']}")
    print(f"Content preview: {result['content'][:500]}...")

