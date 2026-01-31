#!/usr/bin/env python3
"""
Run RAGAS evaluation on the system to generate quality metrics.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "backend" / "src"))

from src.evaluation.ragas_eval import RAGEvaluator
from src.retrieval.hybrid import HybridRetriever
from src.generation.llm import LLMGenerator
from src.retrieval.vector_store import VectorStore
from src.retrieval.bm25_store import BM25Store
from src.retrieval.reranker import Reranker
from src.retrieval.cache import SemanticCache
from src.core.config import get_settings
import redis.asyncio as redis

# Test dataset
TEST_QUESTIONS = [
    "What is machine learning?",
    "How do neural networks work?",
    "What are the best practices in data science?",
    "What are the main components of cloud architecture?",
    "What are the phases of software development lifecycle?",
    "How does machine learning enable systems to improve?",
    "What is the role of artificial neurons in neural networks?",
    "Why is data quality important in data science?",
    "What are the benefits of cloud computing?",
    "What is the purpose of the planning phase in SDLC?",
]

async def run_evaluation():
    """Run RAGAS evaluation on test questions"""
    print("🔍 Starting RAGAS evaluation...")
    
    # Initialize components
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL)
    
    vector_store = VectorStore()
    bm25_store = BM25Store(redis_client)
    reranker = Reranker()
    cache = SemanticCache(redis_client)
    
    retriever = HybridRetriever(
        vector_store=vector_store,
        bm25_store=bm25_store,
        reranker=reranker,
        cache=cache,
    )
    
    llm = LLMGenerator()
    evaluator = RAGEvaluator()
    
    # Generate answers
    print("\n📝 Generating answers for test questions...")
    answers = []
    contexts = []
    
    for i, question in enumerate(TEST_QUESTIONS):
        print(f"Processing question {i+1}/{len(TEST_QUESTIONS)}: {question}")
        
        try:
            # Retrieve
            results = await retriever.retrieve(question, use_cache=False)
            context = [r.content for r in results]
            contexts.append(context)
            
            # Generate
            answer = await llm.generate(question, results)
            answers.append(answer)
            
            print(f"✅ Generated answer (length: {len(answer)} chars)")
            
        except Exception as e:
            print(f"❌ Failed to process question: {str(e)}")
            answers.append("Error generating answer")
            contexts.append([])
    
    # Run evaluation
    print("\n📊 Running RAGAS evaluation...")
    try:
        scores = await evaluator.evaluate_batch(
            questions=TEST_QUESTIONS,
            answers=answers,
            contexts=contexts,
        )
        
        print("\n=== RAGAS EVALUATION RESULTS ===")
        for metric, score in scores.items():
            print(f"{metric}: {score:.3f}")
        
        if evaluator.meets_production_standards(scores):
            print("\n✅ MEETS PRODUCTION STANDARDS")
        else:
            print("\n❌ BELOW PRODUCTION STANDARDS")
        
        # Print detailed analysis
        print("\n📈 Detailed Analysis:")
        print(f"- Faithfulness: {scores['faithfulness']:.3f} (>0.90 required)")
        print(f"- Answer Relevancy: {scores['answer_relevancy']:.3f} (>0.85 required)")
        print(f"- Context Precision: {scores['context_precision']:.3f} (>0.80 required)")
        print(f"- Context Recall: {scores['context_recall']:.3f}")
        
        return scores
        
    except Exception as e:
        print(f"❌ Evaluation failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(run_evaluation())
