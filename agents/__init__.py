"""
Multi-Agent System for Research Paper Review
"""
from agents.reader_agent import ReaderAgent
from agents.meta_reviewer_agent import MetaReviewerAgent
from agents.critic_agent import CriticAgent
from agents.orchestration import get_orchestrator, SimpleOrchestrator

__all__ = [
    'ReaderAgent',
    'MetaReviewerAgent',
    'CriticAgent',
    'get_orchestrator',
    'SimpleOrchestrator'
]

