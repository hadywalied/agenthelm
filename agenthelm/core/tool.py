import inspect
from functools import wraps
from typing import Any, Callable

# A central registry for all tools
TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def tool(
    inputs: dict = None,
    outputs: dict = None,
    side_effects: list[str] = None,
    max_cost: float = 0.0,
    requires_approval: bool = False,
    retries: int = 0,
    compensating_tool: str = None,
    timeout: float = 30.0,
    tags: list[str] = None,
):
    """
    A decorator to register a function as a tool in the orchestration framework.
    If 'inputs' or 'outputs' are not provided, they will be inferred from the function's type hints.
    """

    def tool_decorator(func: Callable) -> Callable:
        """This is the actual decorator that wraps the function and builds the contract."""
        tool_name = func.__name__

        # --- Introspection Logic ---
        sig = inspect.signature(func)

        # Infer inputs from type hints if not provided
        introspected_inputs = {
            param.name: param.annotation.__name__
            for param in sig.parameters.values()
            if param.kind == param.POSITIONAL_OR_KEYWORD
        }

        # Infer outputs from return type hint if not provided
        introspected_outputs = {}
        if sig.return_annotation is not inspect.Signature.empty:
            # For simplicity, we'll assume the output is a dict with a single key 'result'
            introspected_outputs = {"result": sig.return_annotation.__name__}

        # --- Contract Creation ---
        final_inputs = inputs if inputs is not None else introspected_inputs
        final_outputs = outputs if outputs is not None else introspected_outputs

        contract = {
            "inputs": final_inputs,
            "outputs": final_outputs,
            "side_effects": side_effects or [],
            "max_cost": max_cost,
            "requires_approval": requires_approval,
            "retries": retries,
            "compensating_tool": compensating_tool,
            "timeout": timeout,
            "tags": tags or [],
        }

        # Register the tool and its contract
        TOOL_REGISTRY[tool_name] = {"function": func, "contract": contract}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # The orchestrator will use the registry to perform checks
            # before this wrapper is ever called.
            return func(*args, **kwargs)

        return wrapper

    return tool_decorator
