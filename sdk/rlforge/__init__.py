from rlforge.client import RLForgeClient

_default_client = None


def configure(api_url="https://rlforge.ai", api_key=None):
    """Configure the default RLForge client."""
    global _default_client
    _default_client = RLForgeClient(api_url=api_url, api_key=api_key)


def _get_client():
    global _default_client
    if _default_client is None:
        _default_client = RLForgeClient()
    return _default_client


def make(env_slug_or_id, **kwargs):
    """Create a remote environment session (Gymnasium-compatible wrapper)."""
    return _get_client().make(env_slug_or_id, **kwargs)


def generate(description, domain=None, difficulty="medium"):
    """Generate a new environment from natural language description."""
    return _get_client().generate(description, domain=domain, difficulty=difficulty)


def list_envs(domain=None, difficulty=None, search=None, limit=20):
    """List published environments from the catalog."""
    return _get_client().list_envs(
        domain=domain, difficulty=difficulty, search=search, limit=limit
    )


def get_env(slug_or_id):
    """Get environment details."""
    return _get_client().get_env(slug_or_id)
