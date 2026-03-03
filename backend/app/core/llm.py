"""
LLM with API key rotation.
"""
import os
import time
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings

_rate_limited: dict[str, float] = {}


def _get_api_keys() -> list[str]:
    """Load all API keys — tries settings object and os.environ."""
    all_keys = []

    # Method 1: settings object 
    try:
        from app.core.config import settings
        # Single key
        single = getattr(settings, 'GOOGLE_API_KEY', '').strip()
        if single and single.startswith('AIzaSy') and len(single) > 30:
            all_keys.append(single)
        # Pool of keys
        pool_str = getattr(settings, 'GOOGLE_API_KEYS', '').strip()
        if pool_str:
            for k in pool_str.split(','):
                k = k.strip()
                if k.startswith('AIzaSy') and len(k) > 30 and k not in all_keys:
                    all_keys.append(k)
    except Exception:
        pass

    # Method 2: direct os.environ fallback
    if not all_keys:
        for env_var in ['GOOGLE_API_KEYS', 'GOOGLE_API_KEY']:
            val = os.environ.get(env_var, '').strip()
            if val:
                for k in val.split(','):
                    k = k.strip()
                    if k.startswith('AIzaSy') and len(k) > 30 and k not in all_keys:
                        all_keys.append(k)

    return all_keys


# Keys permanently blocked (403 denied access)
_blocked_keys: set = set()


def _get_best_key() -> str:
    """Get a non-rate-limited, non-blocked key."""
    keys = _get_api_keys()

    if not keys:
        raise ValueError("No valid Google API keys found. Check GOOGLE_API_KEY in .env")

    now = time.time()
    # Skip rate-limited AND permanently blocked keys
    available = [k for k in keys
                 if _rate_limited.get(k, 0) < now
                 and k not in _blocked_keys]

    if not available:
        # Try rate-limited keys as last resort (they may have reset)
        not_blocked = [k for k in keys if k not in _blocked_keys]
        if not_blocked:
            print(f"  All keys rate limited — retrying least-limited")
            return min(not_blocked, key=lambda k: _rate_limited.get(k, 0))
        raise ValueError("All API keys are blocked or exhausted")

    key = random.choice(available)
    print(f" Key pool: {len(available)}/{len(keys)} available")
    return key


def mark_key_rate_limited(key: str, seconds: int = 86400):
    """Mark a key as rate limited."""
    _rate_limited[key] = time.time() + seconds
    keys = _get_api_keys()
    available = sum(1 for k in keys if _rate_limited.get(k, 0) < time.time() and k not in _blocked_keys)
    print(f" Key rate limited. {available}/{len(keys)} remaining")


def mark_key_blocked(key: str):
    """Permanently block a key (403 denied access)."""
    _blocked_keys.add(key)
    keys = _get_api_keys()
    available = len([k for k in keys if k not in _blocked_keys])
    print(f" Key permanently blocked (403). {available}/{len(keys)} remaining")


_mark_rate_limited = mark_key_rate_limited


# Track last key used — for rotation on 429
_last_key_used: list[str] = [""]


def get_llm(temperature: float = 0.3, model: str = "gemini-2.5-flash") -> ChatGoogleGenerativeAI:
    """Get LLM with best available API key."""
    key = _get_best_key()
    _last_key_used[0] = key  # Track for rotation
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=key,
        temperature=temperature,
        max_retries=0,  # No internal retries — we handle rotation ourselves
    )
    # Attach key to llm object for easy rotation
    llm._zyra_api_key = key
    return llm


def rotate_current_key():
    """Mark current key as rate limited and return new LLM."""
    key = _last_key_used[0]
    if key:
        mark_key_rate_limited(key, seconds=86400)
    return get_llm()


def get_embeddings():
    """Free local embeddings — no API key needed."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )