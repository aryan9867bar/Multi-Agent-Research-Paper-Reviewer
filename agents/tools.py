"""
Tools for agents to use
"""
import os
import json
import requests
from typing import List, Dict, Optional
import arxiv
import PyPDF2
import pdfplumber
from pathlib import Path


class FileIOTool:
    """File I/O operations"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def read_file(self, filepath: str) -> str:
        """Read a text file"""
        full_path = self.base_dir / filepath
        if not full_path.exists():
            return f"Error: File {filepath} not found"
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, filepath: str, content: str) -> bool:
        """Write content to a file"""
        full_path = self.base_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    def list_files(self, directory: str = "") -> List[str]:
        """List files in a directory"""
        dir_path = self.base_dir / directory
        if not dir_path.exists():
            return []
        return [f.name for f in dir_path.iterdir() if f.is_file()]


class ArxivAPITool:
    """Arxiv API client for fetching papers"""
    
    def __init__(self):
        self.client = arxiv.Client()
    
    def search_papers(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for papers on Arxiv"""
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = []
            for paper in self.client.results(search):
                results.append({
                    'id': paper.entry_id,
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'summary': paper.summary,
                    'published': paper.published.isoformat(),
                    'pdf_url': paper.pdf_url,
                    'categories': paper.categories
                })
            
            return results
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Get a specific paper by Arxiv ID"""
        try:
            # Remove 'arxiv:' prefix if present
            paper_id = paper_id.replace('arxiv:', '').replace('arXiv:', '')
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search), None)
            
            if paper:
                return {
                    'id': paper.entry_id,
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'summary': paper.summary,
                    'published': paper.published.isoformat(),
                    'pdf_url': paper.pdf_url,
                    'categories': paper.categories
                }
            return None
        except Exception as e:
            return {'error': str(e)}
    
    def download_pdf(self, pdf_url: str, save_path: str) -> bool:
        """Download PDF from URL"""
        try:
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return False


class PDFExtractorTool:
    """Extract text from PDF files"""
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return f"Error: PDF file {pdf_path} not found"
            
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF"""
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                return {'error': f'PDF file {pdf_path} not found'}
            
            metadata = {}
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'num_pages': len(pdf_reader.pages)
                    }
                else:
                    metadata = {'num_pages': len(pdf_reader.pages)}
            
            return metadata
        except Exception as e:
            return {'error': str(e)}


class WebCrawlerTool:
    """Simple web crawler for fetching web content"""
    
    def fetch_url(self, url: str) -> str:
        """Fetch content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to 5000 chars
        except Exception as e:
            return f"Error fetching URL: {str(e)}"


# Initialize tool instances
file_io = FileIOTool()
arxiv_api = ArxivAPITool()
pdf_extractor = PDFExtractorTool()
web_crawler = WebCrawlerTool()

