from fastapi import FastAPI, HTTPException
from .approval_models import TaskRequest, ReviewRequest
from .approval_workflow import ApprovalWorkflow

app = FastAPI(title="Week 28 Human-in-the-Loop Approval API")
workflow = ApprovalWorkflow()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tasks")
def submit_task(req: TaskRequest):
    return workflow.submit(req)

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    try:
        return workflow.repository.get(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/approvals/pending")
def pending():
    return workflow.repository.pending()

@app.post("/approvals/review")
def review(req: ReviewRequest):
    try:
        return workflow.review(req.task_id, req.decision, req.reviewer, req.modified_action, req.comment)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
