class ApprovalRepository:
    def __init__(self):
        self.items = {}

    def save(self, task_id, record):
        self.items[task_id] = record
        return record

    def get(self, task_id):
        if task_id not in self.items:
            raise KeyError(f"Task not found: {task_id}")
        return self.items[task_id]

    def pending(self):
        return [v for v in self.items.values() if v.get("state") == "pending_review"]
