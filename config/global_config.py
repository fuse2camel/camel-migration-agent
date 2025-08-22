"""
Global configuration module that loads environment variables
This should be imported at the top of each workflow module
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Find the project root directory (where .env file is located)
def find_project_root():
    """Find the project root by looking for .env file"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / '.env').exists():
            return parent
    return Path.cwd()

# Load environment variables from .env file
PROJECT_ROOT = find_project_root()
ENV_FILE = PROJECT_ROOT / '.env'

# Load the .env file
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)
    print(f"[Config] Loaded environment from: {ENV_FILE}")
else:
    print(f"[Config] Warning: .env file not found at {ENV_FILE}")

# Export commonly used environment variables
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
OPENAI_API_KEY = os.getenv("MODEL_API_KEY")  # Fallback to MODEL_API_KEY
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
MODEL_MODEL = os.getenv("MODEL_MODEL")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "2000"))


# Validate critical environment variables
def validate_config():
    """Validate that critical environment variables are set"""
    errors = []
    
    if not MODEL_API_KEY:
        errors.append("MODEL_API_KEY is not set in .env file")
    
    if errors:
        print("[Config] ❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        print(f"\nPlease ensure your .env file at {ENV_FILE} contains:")
        print("  MODEL_API_KEY=your_api_key_here")
        return False
    
    print("[Config] ✓ Configuration validated successfully")
    return True

# Auto-validate on import
CONFIG_VALID = validate_config()

# Helper function to get config as dict
def get_config_dict():
    """Get all config values as a dictionary"""
    return {
        "MODEL_API_KEY": MODEL_API_KEY,
        "MODEL_BASE_URL": MODEL_BASE_URL,
        "MODEL_MODEL": MODEL_MODEL,
        "MODEL_TEMPERATURE": MODEL_TEMPERATURE,
        "MODEL_MAX_TOKENS": MODEL_MAX_TOKENS,
        "ENV_FILE": str(ENV_FILE),
    }

# Print config summary
def print_config_summary():
    """Print a summary of the current configuration"""
    print("\n" + "="*60)
    print("Super-Writer Configuration Summary")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Environment File: {ENV_FILE}")
    print(f"API Endpoint: {MODEL_BASE_URL}")
    print(f"Model: {MODEL_MODEL}")
    print(f"Temperature: {MODEL_TEMPERATURE}")
    print(f"Max Tokens: {MODEL_MAX_TOKENS}")
    print(f"API Key: {'✓ Set' if MODEL_API_KEY else '✗ Not Set'}")
    print("="*60 + "\n")

if __name__ == "__main__":
    # When run directly, print configuration summary
    print_config_summary()