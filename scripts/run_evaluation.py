"""
Run evaluations on GraphRAG pipeline
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langsmith import Client
from langsmith.evaluation import evaluate
from app.pipelines.graphrag_pipeline import GraphRAGPipeline

def entity_extraction_accuracy(outputs: dict, reference_outputs: dict) -> dict:
    """Custom evaluator for entity extraction"""
    predicted = set(e["entity_name"] for e in outputs.get("entities", []))
    expected = set(e["entity_name"] for e in reference_outputs.get("expected_entities", []))
    
    if not expected:
        return {"score": 0, "comment": "No expected entities"}
    
    correct = len(predicted & expected)
    precision = correct / len(predicted) if predicted else 0
    recall = correct / len(expected)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "score": f1,
        "comment": f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}"
    }

async def run_pipeline_evaluation():
    """Run evaluation on pipeline"""
    pipeline = GraphRAGPipeline()
    
    async def predict(inputs: dict) -> dict:
        """Wrapper to run pipeline on test inputs"""
        result = await pipeline._map_entities({
            "document_id": "eval_test",
            "sections": [inputs],
            "temp_entities": [],
            "errors": []
        })
        return {"entities": result["temp_entities"]}
    
    # Run evaluation
    results = evaluate(
        predict,
        data="graphrag_entity_extraction_eval",
        evaluators=[entity_extraction_accuracy],
        experiment_prefix="graphrag_v1"
    )
    
    print(f"Evaluation complete. View at: https://smith.langchain.com/")
    return results

if __name__ == "__main__":
    asyncio.run(run_pipeline_evaluation())
