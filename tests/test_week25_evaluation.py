import json
from pathlib import Path
from app.evaluation_engine import EvaluationEngine
from app.evaluation_models import CONFIGS
from app.evaluation_metrics import exact_match, retrieval_recall, citation_accuracy, hallucination_rate, field_accuracy
from app.evaluation_report import generate_markdown

def dataset():
    return json.loads(Path('benchmark_data/week25_benchmark.json').read_text())

def test_metrics_basics():
    assert exact_match('A','a') == 1
    assert retrieval_recall(['a','b'],['a']) == 0.5
    assert citation_accuracy(['a'],['a']) == 1
    assert hallucination_rate(1,4) == 0.25
    assert field_accuracy({'x':'1'},{'x':'1'}) == 1

def test_two_configs_exist():
    assert {'baseline','improved'} <= set(CONFIGS)

def test_benchmark_minimum_cases():
    assert len(dataset()) >= 10

def test_engine_runs_baseline():
    r = EvaluationEngine(CONFIGS['baseline']).run(dataset())
    assert len(r['cases']) == len(dataset())

def test_engine_runs_improved():
    r = EvaluationEngine(CONFIGS['improved']).run(dataset())
    assert r['summary']['answer_correctness'] >= 0.9

def test_improved_retrieval_not_worse():
    a = EvaluationEngine(CONFIGS['baseline']).run(dataset())['summary']
    b = EvaluationEngine(CONFIGS['improved']).run(dataset())['summary']
    assert b['retrieval_accuracy'] >= a['retrieval_accuracy']

def test_improved_hallucination_not_worse():
    a = EvaluationEngine(CONFIGS['baseline']).run(dataset())['summary']
    b = EvaluationEngine(CONFIGS['improved']).run(dataset())['summary']
    assert b['hallucination_rate'] <= a['hallucination_rate']

def test_report_generation(tmp_path):
    rs = [EvaluationEngine(c).run(dataset()) for c in CONFIGS.values()]
    p = generate_markdown(rs, tmp_path/'report.md')
    assert p.exists()
