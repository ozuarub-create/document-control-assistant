# Week 25 Architecture

```text
Benchmark Dataset
      |
      v
Configuration Registry ---> Evaluation Engine ---> Metric Calculators
      |                              |
      |                              v
      |                       Per-case Results
      |                              |
      v                              v
Comparison Runner ---------> Historical Repository
                                   |
                                   v
                           Markdown Report / API
```
