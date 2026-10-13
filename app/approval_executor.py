class ActionExecutor:
    def execute(self, action: str, task):
        return {
            "executed": True,
            "action": action,
            "document_id": task["request"]["document_id"],
            "message": "Approved action executed successfully",
        }
