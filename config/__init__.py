"""Config package.
- Exposes a singleton `settings` for easy imports across the app.
- Keeps config files (YAML) and dynamic flags (cooldown.py) in one place.
"""
from .settings import settings  # noqa: F401
