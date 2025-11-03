class ApprovalHandler:
    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        raise NotImplementedError()


class CliHandler(ApprovalHandler):
    def request_approval(self, tool_name: str, arguments: dict) -> bool:
        return (
            input(
                f"Approve execution for tool {tool_name} with arguments {arguments}? (y/n): "
            ).lower()
            == "y"
        )
