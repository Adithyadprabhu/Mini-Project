"""
Entry point to run the Incident Prioritization Agent API or run the prototype evaluation CLI.
"""

import argparse
import sys
import uvicorn
from agent.data_loader import get_data_loader
from agent.evaluator import PrototypeEvaluator
from agent.scoring_engine import PriorityScoringEngine


def run_evaluation_cli(sample_size: int = 2000):
    print("=" * 70)
    print("ATLANTA INCIDENT PRIORITIZATION AGENT - PROTOTYPE EVALUATION")
    print("=" * 70)
    loader = get_data_loader()
    engine = PriorityScoringEngine(data_loader=loader)
    evaluator = PrototypeEvaluator(engine=engine, data_loader=loader)

    print(f"Loading historical incidents (sample size = {sample_size})...")
    summary = evaluator.evaluate_sample(sample_size=sample_size)

    print("\n--- PROTOTYPE EVALUATION RESULTS ---")
    print(f"Evaluated sample size: {summary.evaluated_sample_size}")
    print(f"Overall proxy concordance: {summary.overall_proxy_concordance * 100:.2f}%")
    print("\nPer-Class Performance against Proxy Labels:")
    for cls_name, metrics in summary.per_class_metrics.items():
        print(f"  [{cls_name}]:")
        print(f"    Support in sample: {metrics['support_proxy_count']}")
        print(f"    Precision: {metrics['precision']:.4f} | Recall: {metrics['recall']:.4f} | F1: {metrics['f1_score']:.4f}")

    print("\nMissing Historical Emergency Fields (Treating as Missing, NOT False):")
    for field, count in summary.missing_emergency_fields_handled.items():
        print(f"  {field}: {count} / {summary.evaluated_sample_size} missing (handled with uncertainty buffer)")

    print("\nNotice:")
    print(summary.prototype_warning)
    print("=" * 70)


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    print("=" * 70)
    print(f"Starting Atlanta Incident Prioritization Agent API on http://{host}:{port}")
    print("Interactive Swagger Docs: http://{host}:{port}/docs")
    print("=" * 70)
    uvicorn.run("agent.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atlanta Incident Prioritization Agent")
    parser.add_argument("--evaluate", action="store_true", help="Run rule-based prototyping evaluation CLI")
    parser.add_argument("--sample-size", type=int, default=2000, help="Sample size for evaluation (default: 2000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="API server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="API server port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    if args.evaluate:
        run_evaluation_cli(sample_size=args.sample_size)
    else:
        run_server(host=args.host, port=args.port, reload=args.reload)
