from __future__ import annotations
import json, time
from pathlib import Path
from .evaluation_metrics import exact_match, token_f1, retrieval_recall, citation_accuracy, hallucination_rate, field_accuracy
from .evaluation_models import EvaluationConfig

class EvaluationEngine:
    def __init__(self, config: EvaluationConfig):
        self.config = config

    def _simulate(self, case: dict) -> dict:
        improved = self.config.name == 'improved'
        exp = case['expected']
        answer = exp['answer'] if improved or case['id'] not in {'q03','q07'} else 'Insufficient project information'
        retrieved = exp['source_ids'][:] if improved else exp['source_ids'][:1]
        citations = exp['source_ids'][:] if improved else retrieved[:1]
        metadata = exp.get('metadata', {}).copy()
        if not improved and metadata:
            first = next(iter(metadata))
            metadata[first] = 'unknown'
        classification = exp.get('classification','') if improved or case['id'] != 'q05' else 'unknown'
        unsupported = 0 if improved else (1 if case['id'] in {'q03','q07'} else 0)
        in_tokens = 280 + len(case['question'].split()) * 3
        out_tokens = 80 if improved else 60
        latency = 180 if improved else 120
        return {
            'answer': answer,
            'retrieved_ids': retrieved,
            'citations': citations,
            'metadata': metadata,
            'classification': classification,
            'unsupported_claims': unsupported,
            'total_claims': 3,
            'input_tokens': in_tokens,
            'output_tokens': out_tokens,
            'latency_ms': latency,
        }

    def evaluate_case(self, case: dict) -> dict:
        started = time.perf_counter()
        output = self._simulate(case)
        exp = case['expected']
        latency = output['latency_ms'] + int((time.perf_counter()-started)*1000)
        answer_score = max(exact_match(exp['answer'], output['answer']), token_f1(exp['answer'], output['answer']))
        total_tokens = output['input_tokens'] + output['output_tokens']
        cost = (output['input_tokens']/1000)*self.config.cost_per_1k_input + (output['output_tokens']/1000)*self.config.cost_per_1k_output
        return {
            'id': case['id'],
            'retrieval_accuracy': retrieval_recall(exp['source_ids'], output['retrieved_ids']),
            'answer_correctness': round(answer_score,4),
            'citation_accuracy': citation_accuracy(exp['source_ids'], output['citations']),
            'hallucination_rate': hallucination_rate(output['unsupported_claims'], output['total_claims']),
            'metadata_accuracy': field_accuracy(exp.get('metadata',{}), output['metadata']),
            'classification_accuracy': float(exp.get('classification','') == output['classification']),
            'latency_ms': latency,
            'tokens': total_tokens,
            'estimated_cost_usd': round(cost,6),
        }

    def run(self, dataset: list[dict]) -> dict:
        cases = [self.evaluate_case(c) for c in dataset]
        n = len(cases)
        avg = lambda k: sum(c[k] for c in cases)/n if n else 0
        summary = {
            'configuration': self.config.name,
            'model': self.config.model,
            'prompt_version': self.config.prompt_version,
            'retrieval_accuracy': round(avg('retrieval_accuracy'),4),
            'answer_correctness': round(avg('answer_correctness'),4),
            'citation_accuracy': round(avg('citation_accuracy'),4),
            'hallucination_rate': round(avg('hallucination_rate'),4),
            'metadata_accuracy': round(avg('metadata_accuracy'),4),
            'classification_accuracy': round(avg('classification_accuracy'),4),
            'avg_latency_ms': round(avg('latency_ms'),2),
            'total_tokens': sum(c['tokens'] for c in cases),
            'estimated_cost_usd': round(sum(c['estimated_cost_usd'] for c in cases),6),
        }
        return {'summary': summary, 'cases': cases}
