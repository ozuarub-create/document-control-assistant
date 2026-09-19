# Week 25 Evaluation Methodology

The framework evaluates each configuration against the same benchmark dataset. Metrics include retrieval recall, answer correctness, citation precision, hallucination rate, metadata field accuracy, classification accuracy, response latency, token usage, and estimated cost.

Baseline and improved configurations use identical test cases so changes can be compared fairly. Historical summaries are appended to `results/evaluation_history.jsonl`.
