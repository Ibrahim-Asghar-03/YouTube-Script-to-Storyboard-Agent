import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Force-load environment variables
load_dotenv()

_PROVIDERS = {
    "gemini": lambda: ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0),
    "anthropic": lambda: ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0),
}
_FALLBACK = {"gemini": "anthropic", "anthropic": "gemini"}

def get_llm(node_name: str | None = None):
    override = os.environ.get(f"LLM_PROVIDER_{node_name.upper()}") if node_name else None
    # Default to 'gemini' if LLM_PROVIDER is missing or empty
    provider = (override or os.environ.get("LLM_PROVIDER", "gemini")).lower()
    
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Valid: {list(_PROVIDERS.keys())}")
    
    api_key_name = "GOOGLE_API_KEY" if provider == "gemini" else "ANTHROPIC_API_KEY"
    if not os.environ.get(api_key_name):
        raise ValueError(f"Missing {api_key_name} in environment variables!")
        
    return _PROVIDERS[provider]()

def get_fallback_llm(node_name: str | None = None):
    override = os.environ.get(f"LLM_PROVIDER_{node_name.upper()}") if node_name else None
    provider = (override or os.environ.get("LLM_PROVIDER", "gemini")).lower()
    fallback_provider = _FALLBACK[provider]
    
    api_key_name = "GOOGLE_API_KEY" if fallback_provider == "gemini" else "ANTHROPIC_API_KEY"
    if not os.environ.get(api_key_name):
        raise ValueError(f"Fallback missing {api_key_name} in environment variables!")
        
    return _PROVIDERS[fallback_provider]()