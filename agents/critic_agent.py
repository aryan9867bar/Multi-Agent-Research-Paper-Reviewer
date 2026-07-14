"""
Critic Agent: Validates and critiques the review quality
"""
from typing import Dict, List, Optional
from agents.tools import file_io
from agents.llm_client import get_default_llm


class CriticAgent:
    """Agent responsible for validating review quality and providing feedback"""
    
    def __init__(self, llm=None):
        self.llm = llm or get_default_llm()
        self.name = "Critic"
        self.role = "Validate review quality and ensure completeness"
    
    def process(self, review_data: Dict, original_content: Dict) -> Dict:
        """
        Critique and validate the review
        
        Args:
            review_data: Dict from MetaReviewerAgent with 'review' and 'summary'
            original_content: Original paper content from ReaderAgent
        
        Returns:
            Dict with critique and validation results
        """
        result = {
            'agent': self.name,
            'status': 'success',
            'validation': {},
            'critique': '',
            'improved_review': None
        }
        
        try:
            review = review_data.get('review', {})
            summary = review_data.get('summary', '')
            original = original_content.get('content', '')
            
            if not review and not summary:
                result['status'] = 'error'
                result['critique'] = "No review provided to critique"
                return result
            
            # Validate review completeness
            validation = self._validate_review(review, summary, original)
            result['validation'] = validation
            
            # Provide critique
            critique = self._generate_critique(review, summary, original, validation)
            result['critique'] = critique
            
            # If validation fails, suggest improvements
            if not validation.get('is_complete', False):
                improved = self._suggest_improvements(review, summary, validation)
                result['improved_review'] = improved
            
        except Exception as e:
            result['status'] = 'error'
            result['critique'] = f"Error in CriticAgent: {str(e)}"
        
        return result
    
    def _validate_review(self, review: Dict, summary: str, original: str) -> Dict:
        """Validate if review is complete and accurate"""
        # Truncate all inputs to keep within token limits
        original_preview = original[:1000] if len(original) > 1000 else original
        review_text = str(review.get('review_text', 'N/A'))[:800]
        summary_preview = summary[:500] if len(summary) > 500 else summary
        
        prompt = f"""Validate this review for completeness.

Paper excerpt: {original_preview[:600]}
Review: {review_text[:500]}
Summary: {summary_preview[:300]}

Assess if review covers: strengths, weaknesses, significance.
Rate completeness (0-1). List any missing aspects.
Be brief and specific."""

        system_prompt = """You validate review quality. Be concise and specific."""

        response = self.llm.generate(prompt, system_prompt, temperature=0.6, max_tokens=300)
        
        # Check if review has required sections (more reliable than LLM response)
        review_lower = review_text.lower()
        has_contribution = any(keyword in review_lower for keyword in ['contribution', 'contributes', 'contributed'])
        has_strengths = any(keyword in review_lower for keyword in ['strength', 'strong', 'good', 'well'])
        has_weaknesses = any(keyword in review_lower for keyword in ['weakness', 'weak', 'improve', 'better', 'could'])
        has_significance = any(keyword in review_lower for keyword in ['significance', 'important', 'impact', 'matters', 'relevant'])
        
        # Review is complete if it has most required sections
        sections_found = sum([has_contribution, has_strengths, has_weaknesses, has_significance])
        is_complete = sections_found >= 3  # At least 3 out of 4 sections
        
        # Also check LLM response as secondary indicator
        llm_says_complete = 'complete' in response.lower() or 'yes' in response.lower() or 'good' in response.lower()
        
        # Final decision: complete if either structural check or LLM says so
        final_is_complete = is_complete or llm_says_complete
        
        # Parse response (simplified - in production, use structured output)
        validation = {
            'is_complete': final_is_complete,
            'validation_text': response,
            'missing_aspects': [],
            'accuracy_score': 0.8 if final_is_complete else 0.6,  # Default, would parse from LLM
            'clarity_score': 0.8 if final_is_complete else 0.6
        }
        
        return validation
    
    def _generate_critique(self, review: Dict, summary: str, original: str, validation: Dict) -> str:
        """Generate critique of the review"""
        # Truncate inputs for token limits
        review_text = str(review.get('review_text', 'N/A'))[:800]
        summary_preview = summary[:500] if len(summary) > 500 else summary
        validation_text = str(validation.get('validation_text', 'N/A'))[:500]
        
        prompt = f"""Provide brief critique of this review.

Review: {review_text[:500]}
Summary: {summary_preview[:300]}
Issues: {validation_text[:300]}

Give 2-3 specific suggestions for improvement. Be concise."""

        system_prompt = """You provide constructive feedback. Be specific and brief."""

        critique = self.llm.generate(prompt, system_prompt, temperature=0.7, max_tokens=250)
        
        return critique
    
    def _suggest_improvements(self, review: Dict, summary: str, validation: Dict) -> Dict:
        """Suggest improvements to the review"""
        # Truncate inputs
        review_text = str(review.get('review_text', 'N/A'))[:600]
        summary_preview = summary[:400] if len(summary) > 400 else summary
        validation_text = str(validation.get('validation_text', 'N/A'))[:400]
        
        prompt = f"""Based on this critique, suggest specific improvements to the review:

Current Review:
{review_text}

Current Summary:
{summary_preview}

Validation Issues:
{validation_text}

Provide improved versions or specific suggestions for enhancement."""

        system_prompt = """You are an expert at improving academic reviews. Provide concrete improvements."""

        improved = self.llm.generate(prompt, system_prompt, temperature=0.6, max_tokens=300)
        
        return {
            'improved_text': improved,
            'suggestions': validation.get('missing_aspects', [])
        }


if __name__ == "__main__":
    # Test Critic Agent
    agent = CriticAgent()
    
    # Mock review data
    test_review = {
        'review': {
            'review_text': 'This is a good paper about machine learning...'
        },
        'summary': 'The paper discusses machine learning techniques...'
    }
    
    test_original = {
        'content': 'Original paper content about transformers...'
    }
    
    result = agent.process(test_review, test_original)
    print(f"Status: {result['status']}")
    print(f"Critique preview: {result['critique'][:300]}...")

