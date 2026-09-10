# Week 24 - Document Workflow Agent Architecture

## Architecture

```text
                         +----------------------+
 Uploaded Document ---> |  Workflow Agent API  |
 Task / Objective -----> | POST /workflow-agent|
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |      Planner         |
                         | task + doc preview   |
                         +----------+-----------+
                                    |
                           selects only needed
                                    |
                                    v
        +----------------------------------------------------+
        |                  Agent Tool Registry                |
        | classify | metadata | KB search | completeness      |
        | revisions | summary | review comments | next action |
        +-------------------------+--------------------------+
                                  |
                                  v
                         +----------------------+
                         | Shared Agent Memory  |
                         | intermediate results |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Execution / Audit Log|
                         | reason, tool, result |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Final Workflow Output|
                         | findings + next action|
                         +----------------------+
```

The planner is separate from tool implementations so orchestration can evolve independently. Each tool has a narrow responsibility and writes useful intermediate results into the run memory. This allows later tools to consume earlier results without repeating work.

## Selective Tool Use

A summary request typically executes classification, metadata extraction, and summary generation. A review request adds completeness checking, review comments, and next-action recommendation. A revision-focused task adds revision detection. Knowledge-base search runs only when the task requests related information.

## Auditability

Each step records the planner's reason, execution status, timestamp, and structured tool result. This provides transparent execution history without exposing hidden model chain-of-thought.
