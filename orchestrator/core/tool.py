from functools import wraps
from typing import List, Dict, Any, Callable

# a central registry
# This dictionary will store all our registered tools and their contracts.
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(inputs: dict,
         outputs: dict,
         side_effects: List[str] = None,
         max_cost: float = 0.0,
         requires_approval: bool = False,
         retries: int = 0,
         compensating_tool: str = None):
    """
    A decorator to register a function as a tool in the orchestration framework.
    """
    # Create a dictionary to hold the tool's contract
    contract = {
        "inputs": inputs,
        "outputs": outputs,
        "side_effects": side_effects or [],
        "max_cost": max_cost,
        "requires_approval": requires_approval,
        "retries": retries,
        "compensating_tool": compensating_tool,
    }

    def tool_decorator(func: Callable) -> Callable:
        """This is the actual decorator that wraps the function."""
        tool_name = func.__name__

        # Register the tool and its contract when the code is loaded
        TOOL_REGISTRY[tool_name] = {
            "function": func,
            "contract": contract
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            # For now, the wrapper just executes the function.
            # Later, the orchestrator will use the registry to perform
            # checks before this wrapper is ever called.
            return func(*args, **kwargs)

        return wrapper

    return tool_decorator