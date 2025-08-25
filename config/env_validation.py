"""
Environment validation module
Checks for required environment variables and throws errors if missing
"""

import os
import sys
from typing import List, Dict, Any

REQUIRED_ENV_VARS = {
    'MODEL_API_KEY': 'OpenAI-compatible API key',
    'MODEL_NAME': 'Model name (e.g., gpt-4, qwen-plus-latest)',
    'MODEL_BASE_URL': 'Base URL for the API endpoint',
    'MODEL_TEMPERATURE': 'Temperature setting for the model (0.0-1.0)'
}

def validate_environment() -> Dict[str, Any]:
    """
    Validate that all required environment variables are set.
    
    Returns:
        Dict with validation results
        
    Raises:
        SystemExit: If required environment variables are missing
    """
    missing_vars = []
    invalid_vars = []
    
    for var_name, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(f"  - {var_name}: {description}")
        elif var_name == 'MODEL_TEMPERATURE':
            try:
                temp = float(value)
                if not 0.0 <= temp <= 1.0:
                    invalid_vars.append(f"  - {var_name}: Must be between 0.0 and 1.0, got {value}")
            except ValueError:
                invalid_vars.append(f"  - {var_name}: Must be a number, got {value}")
    
    if missing_vars or invalid_vars:
        error_msg = "❌ Environment validation failed!\n\n"
        
        if missing_vars:
            error_msg += "Missing required environment variables:\n"
            error_msg += "\n".join(missing_vars) + "\n\n"
        
        if invalid_vars:
            error_msg += "Invalid environment variables:\n"
            error_msg += "\n".join(invalid_vars) + "\n\n"
        
        error_msg += "Please create a .env file with the required variables.\n"
        error_msg += "Example .env file:\n"
        error_msg += "MODEL_API_KEY=your_api_key_here\n"
        error_msg += "MODEL_NAME=gpt-4\n"
        error_msg += "MODEL_BASE_URL=https://api.openai.com/v1\n"
        error_msg += "MODEL_TEMPERATURE=0.7\n"
        
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    return {
        "status": "success",
        "message": "All required environment variables are set",
        "variables": {var: "✓ Set" for var in REQUIRED_ENV_VARS.keys()}
    }

def check_env_file_exists() -> bool:
    """Check if .env file exists in the current directory."""
    return os.path.exists('.env')

if __name__ == "__main__":
    validate_environment()
    print("✅ Environment validation passed!")