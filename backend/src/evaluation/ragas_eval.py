from typing import List, Dict
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset
import asyncio

class RAGEvaluator:
    """
    Evaluate RAG system using RAGAS metrics
    
    Metrics:
    - Faithfulness: Is answer grounded in context?
    - Answer Relevancy: Does answer address the question?
    - Context Recall: Did retrieval get all relevant info?
    - Context Precision: Are retrieved docs relevant?
    """
    
    def __init__(self):
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ]
    
    async def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str] = None,
    ) -> Dict[str, float]:
        """
        Evaluate a batch of Q&A pairs
        
        Returns:
            Dictionary of metric scores (0-1)
        """
        
        # Prepare dataset
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }
        
        if ground_truths:
            data["ground_truth"] = ground_truths
        
        dataset = Dataset.from_dict(data)
        
        # Run evaluation
        results = evaluate(dataset, metrics=self.metrics)
        
        return {
            "faithfulness": results["faithfulness"],
            "answer_relevancy": results["answer_relevancy"],
            "context_recall": results["context_recall"],
            "context_precision": results["context_precision"],
        }
    
    def meets_production_standards(self, scores: Dict[str, float]) -> bool:
        """
        Check if scores meet production thresholds
        
        Thresholds:
        - Faithfulness: >0.90 (answers must be grounded)
        - Answer Relevancy: >0.85 (answers must be on-topic)
        - Context Precision: >0.80 (retrieval must be precise)
        """
        
        return (
            scores.get("faithfulness", 0) > 0.90 and
            scores.get("answer_relevancy", 0) > 0.85 and
            scores.get("context_precision", 0) > 0.80
        )
