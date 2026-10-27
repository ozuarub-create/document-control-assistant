# Week 30 Project Intelligence Agent Architecture

```text
User Request
   |
   v
Investigation Planner
   |
   v
Project Intelligence Agent
   |---- Search / Status tools
   |---- Relationship traversal
   |---- Conflict detector
   |---- Evidence & citation engine
   |---- Evidence sufficiency check
   v
Findings Engine
   |
   +--> FACTS (directly supported)
   +--> INFERENCES (evidence-backed interpretation)
   +--> RECOMMENDATIONS (management action)
   v
Executive Management Report
   |
   +--> JSON
   +--> Markdown
   +--> Complete execution trace
```

The agent never upgrades an inference to a fact without direct supporting evidence.
