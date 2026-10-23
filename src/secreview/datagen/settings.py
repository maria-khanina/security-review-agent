"""Project root discovery and access to the generator settings."""

from pathlib import Path

from secreview.datagen.generation_settings import GENERATION_SETTINGS
from secreview.datagen.settings_models import GenerationSettings

PROJECT_MARKER = "pyproject.toml"


def find_project_root() -> Path:
    """Locate the repository root of the security_agent project."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / PROJECT_MARKER).exists():
            return candidate
    raise FileNotFoundError(PROJECT_MARKER)


PROJECT_ROOT = find_project_root()


def project_path(relative_path: str) -> Path:
    """Resolve a path from the settings against the project root."""
    return PROJECT_ROOT / relative_path


def load_settings() -> GenerationSettings:
    """Return the generator settings."""
    return GENERATION_SETTINGS
