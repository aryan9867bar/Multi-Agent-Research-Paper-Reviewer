"""
Multi-Agent Orchestration using LangGraph
"""
import sys
from pathlib import Path
from typing import Dict, List, TypedDict, Annotated
import operator

# Add parent directory to path to enable running directly
sys.path.append(str(Path(__file__).parent.parent))

# Try to import LangGraph, but fallback gracefully if not available
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from agents.reader_agent import ReaderAgent
from agents.meta_reviewer_agent import MetaReviewerAgent
from agents.critic_agent import CriticAgent


class AgentState(TypedDict):
    """State shared between agents"""
    input: str  # Original input (paper ID, PDF path, or URL)
    input_type: str  # 'arxiv_id', 'pdf_path', or 'url'
    reader_output: Dict
    reviewer_output: Dict
    critic_output: Dict
    final_output: Dict
    errors: List[str]


class PaperReviewOrchestrator:
    """Orchestrates the multi-agent paper review system"""
    
    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is not available. Use SimpleOrchestrator instead.")
        
        self.reader = ReaderAgent()
        self.reviewer = MetaReviewerAgent()
        self.critic = CriticAgent()
        
        # Build graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("reader", self._reader_node)
        workflow.add_node("reviewer", self._reviewer_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define edges
        workflow.set_entry_point("reader")
        workflow.add_edge("reader", "reviewer")
        workflow.add_edge("reviewer", "critic")
        workflow.add_edge("critic", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow
    
    def _reader_node(self, state: AgentState) -> AgentState:
        """Reader agent node"""
        try:
            input_data = {
                'type': state.get('input_type', 'arxiv_id'),
                'value': state['input'],
                'extract_full_text': True
            }
            result = self.reader.process(input_data)
            state['reader_output'] = result
            if result.get('status') == 'error':
                state['errors'] = state.get('errors', []) + [f"Reader error: {result.get('content', 'Unknown error')}"]
        except Exception as e:
            state['errors'] = state.get('errors', []) + [f"Reader exception: {str(e)}"]
            state['reader_output'] = {'status': 'error', 'content': str(e)}
        
        return state
    
    def _reviewer_node(self, state: AgentState) -> AgentState:
        """Reviewer agent node"""
        try:
            reader_output = state.get('reader_output', {})
            if reader_output.get('status') == 'error':
                state['reviewer_output'] = {'status': 'error', 'summary': 'Skipped due to reader error'}
                return state
            
            result = self.reviewer.process(reader_output)
            state['reviewer_output'] = result
            if result.get('status') == 'error':
                state['errors'] = state.get('errors', []) + [f"Reviewer error: {result.get('summary', 'Unknown error')}"]
        except Exception as e:
            state['errors'] = state.get('errors', []) + [f"Reviewer exception: {str(e)}"]
            state['reviewer_output'] = {'status': 'error', 'summary': str(e)}
        
        return state
    
    def _critic_node(self, state: AgentState) -> AgentState:
        """Critic agent node"""
        try:
            reviewer_output = state.get('reviewer_output', {})
            reader_output = state.get('reader_output', {})
            
            if reviewer_output.get('status') == 'error':
                state['critic_output'] = {'status': 'error', 'critique': 'Skipped due to reviewer error'}
                return state
            
            result = self.critic.process(reviewer_output, reader_output)
            state['critic_output'] = result
            if result.get('status') == 'error':
                state['errors'] = state.get('errors', []) + [f"Critic error: {result.get('critique', 'Unknown error')}"]
        except Exception as e:
            state['errors'] = state.get('errors', []) + [f"Critic exception: {str(e)}"]
            state['critic_output'] = {'status': 'error', 'critique': str(e)}
        
        return state
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize and compile results"""
        final_output = {
            'input': state.get('input', ''),
            'input_type': state.get('input_type', ''),
            'reader': state.get('reader_output', {}),
            'reviewer': state.get('reviewer_output', {}),
            'critic': state.get('critic_output', {}),
            'errors': state.get('errors', []),
            'success': len(state.get('errors', [])) == 0
        }
        
        # Compile final summary
        if final_output['success']:
            reviewer = state.get('reviewer_output', {})
            critic = state.get('critic_output', {})
            
            final_output['summary'] = reviewer.get('summary', '')
            final_output['review'] = reviewer.get('review', {})
            final_output['validation'] = critic.get('validation', {})
            final_output['critique'] = critic.get('critique', '')
        else:
            final_output['summary'] = f"Processing failed with errors: {', '.join(final_output['errors'])}"
        
        state['final_output'] = final_output
        return state
    
    def process(self, input_value: str, input_type: str = 'arxiv_id') -> Dict:
        """
        Process a paper review request
        
        Args:
            input_value: Paper ID, PDF path, or URL
            input_type: 'arxiv_id', 'pdf_path', or 'url'
        
        Returns:
            Final output dictionary
        """
        initial_state = {
            'input': input_value,
            'input_type': input_type,
            'reader_output': {},
            'reviewer_output': {},
            'critic_output': {},
            'final_output': {},
            'errors': []
        }
        
        # Run the graph
        final_state = self.app.invoke(initial_state)
        
        return final_state['final_output']


# Simple non-LangGraph version for fallback
class SimpleOrchestrator:
    """Simple sequential orchestrator (fallback if LangGraph not available)"""
    
    def __init__(self):
        self.reader = ReaderAgent()
        self.reviewer = MetaReviewerAgent()
        self.critic = CriticAgent()
    
    def process(self, input_value: str, input_type: str = 'arxiv_id') -> Dict:
        """Process sequentially"""
        errors = []
        
        # Step 1: Reader
        try:
            input_data = {'type': input_type, 'value': input_value, 'extract_full_text': True}
            reader_output = self.reader.process(input_data)
            if reader_output.get('status') == 'error':
                errors.append(f"Reader: {reader_output.get('content', 'Unknown error')}")
        except Exception as e:
            errors.append(f"Reader exception: {str(e)}")
            reader_output = {'status': 'error', 'content': str(e)}
        
        # Step 2: Reviewer
        reviewer_output = {}
        if reader_output.get('status') != 'error':
            try:
                reviewer_output = self.reviewer.process(reader_output)
                if reviewer_output.get('status') == 'error':
                    errors.append(f"Reviewer: {reviewer_output.get('summary', 'Unknown error')}")
            except Exception as e:
                errors.append(f"Reviewer exception: {str(e)}")
                reviewer_output = {'status': 'error', 'summary': str(e)}
        else:
            reviewer_output = {'status': 'error', 'summary': 'Skipped due to reader error'}
        
        # Step 3: Critic
        critic_output = {}
        if reviewer_output.get('status') != 'error':
            try:
                critic_output = self.critic.process(reviewer_output, reader_output)
                if critic_output.get('status') == 'error':
                    errors.append(f"Critic: {critic_output.get('critique', 'Unknown error')}")
            except Exception as e:
                errors.append(f"Critic exception: {str(e)}")
                critic_output = {'status': 'error', 'critique': str(e)}
        else:
            critic_output = {'status': 'error', 'critique': 'Skipped due to reviewer error'}
        
        # Finalize
        final_output = {
            'input': input_value,
            'input_type': input_type,
            'reader': reader_output,
            'reviewer': reviewer_output,
            'critic': critic_output,
            'errors': errors,
            'success': len(errors) == 0
        }
        
        if final_output['success']:
            final_output['summary'] = reviewer_output.get('summary', '')
            final_output['review'] = reviewer_output.get('review', {})
            final_output['validation'] = critic_output.get('validation', {})
            final_output['critique'] = critic_output.get('critique', '')
        else:
            final_output['summary'] = f"Processing failed: {', '.join(errors)}"
        
        return final_output


def get_orchestrator(use_langgraph: bool = True):
    """Get orchestrator instance"""
    if use_langgraph:
        try:
            return PaperReviewOrchestrator()
        except Exception as e:
            print(f"LangGraph not available, using simple orchestrator: {e}")
            return SimpleOrchestrator()
    else:
        return SimpleOrchestrator()


if __name__ == "__main__":
    # Test orchestrator
    orchestrator = get_orchestrator(use_langgraph=False)
    
    # Test with Arxiv ID
    result = orchestrator.process("1706.03762", input_type="arxiv_id")
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"\nSummary:\n{result['summary'][:500]}...")
    else:
        print(f"Errors: {result['errors']}")

