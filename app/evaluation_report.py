from __future__ import annotations
from pathlib import Path

METRICS = ['retrieval_accuracy','answer_correctness','citation_accuracy','hallucination_rate','metadata_accuracy','classification_accuracy','avg_latency_ms','total_tokens','estimated_cost_usd']

def generate_markdown(results: list[dict], path='results/week25_comparison_report.md'):
    rows = [r['summary'] for r in results]
    header = '| Configuration | Retrieval | Answer | Citation | Hallucination | Metadata | Classification | Latency ms | Tokens | Cost USD |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|'
    body = []
    for s in rows:
        body.append(f"| {s['configuration']} | {s['retrieval_accuracy']:.2%} | {s['answer_correctness']:.2%} | {s['citation_accuracy']:.2%} | {s['hallucination_rate']:.2%} | {s['metadata_accuracy']:.2%} | {s['classification_accuracy']:.2%} | {s['avg_latency_ms']} | {s['total_tokens']} | {s['estimated_cost_usd']:.6f} |")
    best = max(rows, key=lambda x: x['answer_correctness'] - x['hallucination_rate'])
    text = '# Week 25 Evaluation Comparison Report\n\n' + header + '\n' + '\n'.join(body) + f"\n\n## Observation\n\nHighest answer-correctness minus hallucination score: **{best['configuration']}**.\n"
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8'); return p
