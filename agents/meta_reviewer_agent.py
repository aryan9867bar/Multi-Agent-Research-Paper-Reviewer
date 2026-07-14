"""
MetaReviewer Agent: Reviews and summarizes papers for students
"""
from typing import Dict, List, Optional
from agents.tools import file_io
from agents.llm_client import get_default_llm


class MetaReviewerAgent:
    """Agent responsible for reviewing and summarizing papers"""
    
    def __init__(self, llm=None):
        self.llm = llm or get_default_llm()
        self.name = "MetaReviewer"
        self.role = "Review and summarize research papers in student-friendly language"
    
    def process(self, paper_content: Dict) -> Dict:
        """
        Review and summarize a paper
        
        Args:
            paper_content: Dict from ReaderAgent with 'content' and 'structured_info'
        
        Returns:
            Dict with review and summary
        """
        result = {
            'agent': self.name,
            'status': 'success',
            'review': {},
            'summary': ''
        }
        
        try:
            content = paper_content.get('content', '')
            structured_info = paper_content.get('structured_info', {})
            metadata = paper_content.get('metadata', {})
            
            if not content:
                result['status'] = 'error'
                result['summary'] = "No content provided to review"
                return result
            
            # Generate comprehensive review
            review = self._generate_review(content, structured_info, metadata)
            result['review'] = review
            
            # Generate student-friendly summary
            summary = self._generate_summary(content, structured_info, review)
            result['summary'] = summary
            
            # Save review to file
            paper_title = metadata.get('title', 'unknown_paper')
            safe_title = "".join(c for c in paper_title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
            review_file = f"./data/reviews/{safe_title}_review.json"
            file_io.write_file(review_file, str(result))
            
        except Exception as e:
            result['status'] = 'error'
            result['summary'] = f"Error in MetaReviewerAgent: {str(e)}"
        
        return result
    
    def _generate_review(self, content: str, structured_info: Dict, metadata: Dict) -> Dict:
        """Generate comprehensive, detailed review"""
        # Use more content for better context
        content_preview = content[:2000] if len(content) > 2000 else content
        
        title = metadata.get('title', 'Unknown')
        authors = ', '.join(metadata.get('authors', ['Unknown'])[:5])
        
        # GPT-2 Medium works better with simpler, more direct prompts
        # Generate each section separately for better quality
        
        # 1. Main Contribution
        contribution_prompt = f"""Research Paper Review: {title}

Abstract: {content_preview[:800]}

Question: What is the main contribution of this paper? What problem does it solve? What is novel?

Answer:"""
        contribution = self.llm.generate(contribution_prompt, None, temperature=0.8, max_tokens=120)
        contribution = self._extract_first_sentence(contribution, min_length=50)
        
        # 2. Strengths
        strengths_prompt = f"""Research Paper Review: {title}

Abstract: {content_preview[:800]}

Question: What are the key strengths of this research? List 3-4 specific strengths.

Answer:"""
        strengths = self.llm.generate(strengths_prompt, None, temperature=0.8, max_tokens=150)
        strengths = self._clean_section(strengths, min_length=80)
        
        # 3. Weaknesses
        weaknesses_prompt = f"""Research Paper Review: {title}

Abstract: {content_preview[:800]}

Question: What are the limitations or weaknesses of this research? What could be improved?

Answer:"""
        weaknesses = self.llm.generate(weaknesses_prompt, None, temperature=0.8, max_tokens=120)
        weaknesses = self._clean_section(weaknesses, min_length=60)
        
        # 4. Significance
        significance_prompt = f"""Research Paper Review: {title}

Abstract: {content_preview[:800]}

Question: Why is this research important? What impact could it have? Who would benefit?

Answer:"""
        significance = self.llm.generate(significance_prompt, None, temperature=0.8, max_tokens=120)
        significance = self._extract_first_sentence(significance, min_length=50)
        
        # Combine into structured review
        review_text = f"""**Main Contribution:**
{contribution}

**Strengths:**
{strengths}

**Weaknesses:**
{weaknesses}

**Significance:**
{significance}"""
        
        return {
            'review_text': review_text,
            'structured_info': structured_info
        }
    
    def _extract_first_sentence(self, text: str, min_length: int = 30) -> str:
        """Extract the first meaningful sentence from generated text"""
        if not text:
            return ""
        
        # Remove common prefixes
        text = text.strip()
        prefixes = ["Answer:", "The", "This", "In", "A", "An"]
        for prefix in prefixes:
            if text.startswith(prefix + " "):
                text = text[len(prefix) + 1:].strip()
        
        # Split by sentences
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= min_length:
                return sentence + '.'
        
        # If no good sentence found, return first part
        return text[:200].strip() + ('...' if len(text) > 200 else '')
    
    def _clean_section(self, text: str, min_length: int = 50) -> str:
        """Clean and format a section of text"""
        if not text:
            return ""
        
        # Remove common prefixes
        text = text.strip()
        prefixes = ["Answer:", "The", "This", "Strengths:", "Weaknesses:", "1.", "2.", "3.", "-"]
        for prefix in prefixes:
            if text.startswith(prefix + " "):
                text = text[len(prefix) + 1:].strip()
            elif text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Remove repetition
        sentences = text.split('.')
        seen = set()
        unique_sentences = []
        for s in sentences:
            s = s.strip()
            if not s or len(s) < 10:
                continue
            normalized = ' '.join(s.lower().split())
            if normalized not in seen and len(normalized) > 20:
                seen.add(normalized)
                unique_sentences.append(s)
        
        result = '. '.join(unique_sentences[:3])  # Max 3 sentences per section
        if result and not result.endswith('.'):
            result += '.'
        
        return result if len(result) >= min_length else text[:min_length*2]
    
    def _generate_summary(self, content: str, structured_info: Dict, review: Dict) -> str:
        """Generate comprehensive student-friendly summary"""
        content_preview = content[:1500] if len(content) > 1500 else content
        title = structured_info.get('title', 'Unknown')
        
        # Generate summary with simpler prompt for GPT-2
        summary_prompt = f"""Research Paper Summary: {title}

Abstract: {content_preview[:600]}

Question: Write a brief, student-friendly summary explaining what this paper is about, what problem it solves, and why it matters.

Answer:"""

        summary = self.llm.generate(summary_prompt, None, temperature=0.8, max_tokens=200)
        
        # Clean up but keep it comprehensive
        summary = self._clean_summary(summary)
        
        # Ensure minimum length
        if len(summary) < 150:
            # If too short, try again with more tokens
            summary = self.llm.generate(summary_prompt, None, temperature=0.8, max_tokens=250)
            summary = self._clean_summary(summary)
        
        return summary
    
    def _clean_summary(self, text: str) -> str:
        """Clean up summary text"""
        if not text:
            return ""
        
        # Remove excessive repetition
        sentences = [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 10]
        if not sentences:
            return text
        
        # Keep unique sentences
        seen = set()
        unique_sentences = []
        for s in sentences:
            normalized = ' '.join(s.lower().split())
            if normalized not in seen:
                seen.add(normalized)
                unique_sentences.append(s)
        
        result = '. '.join(unique_sentences[:4])  # Max 4 sentences
        if result and not result.endswith('.'):
            result += '.'
        
        return result


if __name__ == "__main__":
    # Test MetaReviewer Agent
    agent = MetaReviewerAgent()
    
    # Mock paper content
    test_content = {
        'content': 'Sample paper content about machine learning...',
        'structured_info': {
            'main_topic': 'Machine Learning',
            'key_contributions': ['Novel algorithm', 'Better performance']
        },
        'metadata': {
            'title': 'Test Paper',
            'authors': ['Author 1', 'Author 2']
        }
    }
    
    result = agent.process(test_content)
    print(f"Status: {result['status']}")
    print(f"Summary preview: {result['summary'][:300]}...")

