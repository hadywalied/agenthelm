"""AgentHelm CLI configuration management."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

import importlib
from typing import Callable


CONFIG_DIR = Path.home() / ".agenthelm"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "default_model": "mistral/mistral-large-latest",
    "max_iters": 10,
    "api_keys": {},
    "mcp_servers": [],
}


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """
    Load configuration from all sources.

    Priority (highest to lowest):
    1. Environment variables
    2. .env file in current directory
    3. ~/.agenthelm/config.yaml
    4. Defaults
    """
    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Load from config file
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            file_config = yaml.safe_load(f) or {}
            config.update(file_config)

    # Load .env file (sets environment variables)
    load_dotenv()

    # Environment variable overrides
    if os.getenv("AGENTHELM_MODEL"):
        config["default_model"] = os.getenv("AGENTHELM_MODEL")

    return config


def save_config(config: dict[str, Any]):
    """Save configuration to ~/.agenthelm/config.yaml."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_api_key(provider: str) -> str | None:
    """
    Get API key for a provider.

    Checks (in order):
    1. Environment variable (e.g., OPENAI_API_KEY)
    2. Config file api_keys
    """
    # Map provider to env var name
    env_var_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
    }

    # Check environment first
    env_var = env_var_map.get(provider.lower())
    if env_var and os.getenv(env_var):
        return os.getenv(env_var)

    # Fall back to config file
    config = load_config()
    return config.get("api_keys", {}).get(provider.lower())


def set_api_key(provider: str, key: str):
    """Store API key in config file."""
    config = load_config()
    if "api_keys" not in config:
        config["api_keys"] = {}
    config["api_keys"][provider.lower()] = key
    save_config(config)


def init_config():
    """Initialize config directory and file with defaults."""
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
    return CONFIG_FILE


def load_tools_from_string(tools_str: str) -> list[Callable]:
    """
    Load tools from a module:function string.

    Format: "module:func1,func2" or "module.submodule:func"

    Example:
        tools = load_tools_from_string("mytools:search,summarize")
    """
    if not tools_str:
        return []

    tools = []

    for part in tools_str.split(","):
        part = part.strip()
        if ":" in part:
            module_path, func_name = part.rsplit(":", 1)
        else:
            # Assume TOOL_REGISTRY if no module
            from agenthelm.core.tool import TOOL_REGISTRY

            if part in TOOL_REGISTRY:
                tools.append(TOOL_REGISTRY[part]["function"])
            continue

        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            tools.append(func)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Cannot load tool '{part}': {e}")

    return tools
