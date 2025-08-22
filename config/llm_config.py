"""
LLM config
"""
import os
from typing import Optional
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
        
        if not self.api_key:
            raise ValueError(
                "MODEL_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
    
    def get_llm(self, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> ChatOpenAI:

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