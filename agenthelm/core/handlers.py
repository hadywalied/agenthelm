from abc import ABC, abstractmethod


class ApprovalHandler(ABC):
    @abstractmethod
    def request_approval(self, tool_name: str, arguments: dict) -> bool: ...


class AutoApproveHandler(ApprovalHandler):
    """Auto-approve for CI/testing."""

    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        return True


class AutoDenyHandler(ApprovalHandler):
    """Auto-deny (useful for dry-run mode)."""

    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        return False


class CliHandler(ApprovalHandler):
    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        return (
            input(
                f"Approve execution for tool {tool_name} with arguments {arguments}? (y/n): "
            ).lower()
            == "y"
        )
