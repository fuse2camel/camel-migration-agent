"""
Base Agent Class
Provides common functionality for all migration agents
"""
from crewai import Agent
from config.llm_config import get_llm


class BaseAgent:
    """Base class for all migration agents"""
    
    def __init__(self, role: str, goal: str, backstory: str, verbose: bool = True):
        """
        Initialize base agent
        
        Args:
            role: Agent's role
            goal: Agent's goal
            backstory: Agent's backstory
            verbose: Whether to show verbose output
        """
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.verbose = verbose
        
        # Get LLM configuration
        self.llm = get_llm()
        
        # Create the CrewAI agent
        self.agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            verbose=self.verbose,
            llm=self.llm,
            allow_delegation=False,
            max_iter=3
        )
    
    def __str__(self):
        """String representation"""
        return f"{self.__class__.__name__}(role='{self.role}')"
    
    def __repr__(self):
        """Detailed representation"""
        return f"{self.__class__.__name__}(role='{self.role}', goal='{self.goal[:50]}...')"