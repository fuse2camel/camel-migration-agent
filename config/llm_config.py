"""
LLM config
"""
import os
from typing import Optional, Union
from crewai import LLM
from langchain_openai import ChatOpenAI

# Import global configuration (this loads .env automatically)
from config.global_config import (
    MODEL_API_KEY, 
    MODEL_BASE_URL, 
    MODEL_NAME,
    MODEL_TEMPERATURE,
    MODEL_MAX_TOKENS,
    CONFIG_VALID
)

class ModelConfig:
    
    def __init__(self):
        # Use values from global config
        self.api_key = MODEL_API_KEY
        self.model_name = MODEL_NAME
        self.base_url = MODEL_BASE_URL
        self.temperature = MODEL_TEMPERATURE
        self.max_tokens = MODEL_MAX_TOKENS
        
        # For vLLM, API key can be "none" or any placeholder value
        if not self.api_key:
            raise ValueError(
                "MODEL_API_KEY environment variable is required. "
                "Please set it in your .env file (use 'none' for vLLM)."
            )
    
    def get_llm(self, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Union[LLM, ChatOpenAI]:
        # For CrewAI agents, use CrewAI's LLM class with OpenAI-compatible configuration
        # This is required for vLLM compatibility
        if self.base_url and ("localhost" in self.base_url or "0.0.0.0" in self.base_url):
            # Use CrewAI's LLM for local vLLM server
            return LLM(
                model=f"openai/{self.model_name}",  # Prefix with openai/ for OpenAI-compatible servers
                base_url=self.base_url,
                api_key=self.api_key,  # Can be any string for vLLM
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
        else:
            # For actual OpenAI API, use ChatOpenAI
            return ChatOpenAI(
                api_key=self.api_key,
                model=self.model_name,
                base_url=self.base_url,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

# global config
model_config = ModelConfig()

# default LLM instance
default_llm = model_config.get_llm()

# config
creative_llm = model_config.get_llm(temperature=0.9, max_tokens=1000)  # creative writing
analytical_llm = model_config.get_llm(temperature=0.3, max_tokens=1500)  # analytical
structured_llm = model_config.get_llm(temperature=0.1, max_tokens=3000)  # structured output

# Standalone function for backward compatibility
def get_llm(temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Union[LLM, ChatOpenAI]:
    """Get an LLM instance with optional custom parameters"""
    return model_config.get_llm(temperature=temperature, max_tokens=max_tokens)

# Alias for backward compatibility with tests
def get_llm_config(temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Union[LLM, ChatOpenAI]:
    """Alias for get_llm - for backward compatibility"""
    return get_llm(temperature=temperature, max_tokens=max_tokens)