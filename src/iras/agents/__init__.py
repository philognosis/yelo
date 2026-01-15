"""Specialized agents for the IRAS system"""

from iras.agents.researcher import ResearcherAgent
from iras.agents.analyst import AnalystAgent
from iras.agents.fact_checker import FactCheckerAgent
from iras.agents.synthesizer import SynthesizerAgent

__all__ = [
    "ResearcherAgent",
    "AnalystAgent",
    "FactCheckerAgent",
    "SynthesizerAgent",
]
