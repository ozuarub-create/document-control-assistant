import json
from pathlib import Path
from app.evaluation_engine import EvaluationEngine
from app.evaluation_models import CONFIGS
from app.evaluation_repository import EvaluationRepository
from app.evaluation_report import generate_markdown

print('='*76)
print('Week 25 - AI Evaluation and Benchmarking Demo')
print('='*76)
dataset = json.loads(Path('benchmark_data/week25_benchmark.json').read_text())
print('Benchmark scenarios:', len(dataset))
print('Configurations:', ', '.join(CONFIGS))
repo = EvaluationRepository()
results = []
for name, cfg in CONFIGS.items():
    result = EvaluationEngine(cfg).run(dataset)
    repo.append(result)
    results.append(result)
    s = result['summary']
    print(f"\n{name.upper()} | retrieval={s['retrieval_accuracy']:.1%} answer={s['answer_correctness']:.1%} citations={s['citation_accuracy']:.1%} hallucination={s['hallucination_rate']:.1%} latency={s['avg_latency_ms']}ms cost=${s['estimated_cost_usd']:.6f}")
Path('results/demo_week25_results.json').write_text(json.dumps(results, indent=2))
report = generate_markdown(results)
print('\nWeek 25 Demo Complete')
print('- Automated evaluation framework: working')
print('- Benchmark dataset: working')
print('- Two configuration comparison: working')
print('- Historical result storage: working')
print('- Generated report:', report)
