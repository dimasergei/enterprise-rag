#!/usr/bin/env python3
"""
Seed the RAG system with sample documents for testing and demonstration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "backend" / "src"))

from src.ingestion.indexer import DocumentIndexer
from src.retrieval.vector_store import VectorStore
from src.retrieval.bm25_store import BM25Store
from src.core.config import get_settings
import redis.asyncio as redis

# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "title": "Introduction to Machine Learning",
        "content": """
        Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. 
        It focuses on developing computer programs that can access data and use it to learn for themselves.
        
        The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide.
        
        Machine learning algorithms build a mathematical model based on sample data, known as "training data", in order to make predictions or decisions without being explicitly programmed to do so.
        """,
        "metadata": {
            "source": "ml_basics.pdf",
            "category": "technology",
            "author": "ML Team"
        }
    },
    {
        "title": "Neural Networks Fundamentals",
        "content": """
        Neural networks are computing systems vaguely inspired by the biological neural networks that constitute animal brains. 
        Such systems "learn" to perform tasks by considering examples, generally without being programmed with task-specific rules.
        
        A neural network is based on a collection of connected units or nodes called artificial neurons, which loosely model the neurons in a biological brain. 
        Each connection, like the synapses in a biological brain, can transmit a signal to other neurons.
        
        An artificial neuron that receives a signal then processes it and can signal neurons connected to it. The "signal" at a connection is a real number, and the output of each neuron is computed by some non-linear function of the sum of its inputs.
        """,
        "metadata": {
            "source": "neural_networks.pdf",
            "category": "technology",
            "author": "AI Research Team"
        }
    },
    {
        "title": "Data Science Best Practices",
        "content": """
        Data science is an interdisciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge and insights from noisy, structured, and unstructured data.
        
        Key best practices in data science include:
        1. Data Quality: Ensure data is accurate, complete, and consistent
        2. Proper Documentation: Document data sources, transformations, and assumptions
        3. Version Control: Use version control for both code and data
        4. Reproducibility: Ensure results can be reproduced by others
        5. Ethical Considerations: Consider privacy, fairness, and bias in data analysis
        
        Data science combines multiple fields including statistics, data analysis, machine learning, and related methods in order to understand and analyze actual phenomena with data.
        """,
        "metadata": {
            "source": "data_science_guide.pdf",
            "category": "technology",
            "author": "Data Team"
        }
    },
    {
        "title": "Cloud Computing Architecture",
        "content": """
        Cloud computing is the on-demand availability of computer system resources, especially data storage and computing power, without direct active management by the user.
        
        The main components of cloud architecture include:
        - Frontend Platform: The client-side interface
        - Backend Platform: Servers, storage, databases
        - Cloud-based delivery: SaaS, PaaS, IaaS
        - Network: Internet, intranet, intercloud
        
        Benefits of cloud computing include:
        1. Cost Efficiency: Pay only for what you use
        2. Scalability: Scale resources up or down as needed
        3. Accessibility: Access from anywhere with internet
        4. Reliability: Built-in redundancy and backup
        5. Automatic Updates: Providers handle software updates
        """,
        "metadata": {
            "source": "cloud_architecture.pdf",
            "category": "technology",
            "author": "Infrastructure Team"
        }
    },
    {
        "title": "Software Development Lifecycle",
        "content": """
        The Software Development Life Cycle (SDLC) is a systematic process for building software that ensures quality and correctness.
        
        The typical phases of SDLC include:
        1. Planning: Define requirements and scope
        2. Analysis: Analyze requirements and create specifications
        3. Design: Create system architecture and design
        4. Implementation: Write actual code
        5. Testing: Verify software meets requirements
        6. Deployment: Release software to production
        7. Maintenance: Ongoing support and improvements
        
        Modern SDLC approaches include Agile, DevOps, and Continuous Integration/Continuous Deployment (CI/CD) methodologies that emphasize iterative development and rapid delivery.
        """,
        "metadata": {
            "source": "sdlc_guide.pdf",
            "category": "technology",
            "author": "Engineering Team"
        }
    }
]

async def seed_documents():
    """Seed the system with sample documents"""
    print("🚀 Starting document seeding...")
    
    # Initialize components
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL)
    
    vector_store = VectorStore()
    bm25_store = BM25Store(redis_client)
    indexer = DocumentIndexer(vector_store, bm25_store)
    
    # Process each document
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        print(f"\n📄 Processing document {i+1}/{len(SAMPLE_DOCUMENTS)}: {doc['title']}")
        
        try:
            # Create document data
            document_data = {
                "content": doc["content"],
                "metadata": {
                    **doc["metadata"],
                    "title": doc["title"],
                    "document_id": f"sample_doc_{i+1}",
                    "chunk_id": f"sample_doc_{i+1}_0"
                }
            }
            
            # Add chunks to indexer
            chunks = await indexer.ingest_bytes(
                file_bytes=doc["content"].encode('utf-8'),
                filename=doc["metadata"]["source"],
                document_id=f"sample_doc_{i+1}",
                metadata=doc["metadata"]
            )
            
            print(f"✅ Successfully indexed: {doc['title']}")
            print(f"   Chunks processed: {chunks['chunks_processed']}")
            
        except Exception as e:
            print(f"❌ Failed to process {doc['title']}: {str(e)}")
    
    print(f"\n🎉 Seeding complete! Processed {len(SAMPLE_DOCUMENTS)} documents")
    print("\n📊 System is ready for testing!")
    print("Visit http://localhost:3000 to try the chat interface")

if __name__ == "__main__":
    asyncio.run(seed_documents())
