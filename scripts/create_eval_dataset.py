"""
Create evaluation dataset for GraphRAG pipeline
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set environment variables for LangSmith (use actual env vars in production)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "sagewrite-graphrag"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

from langsmith import Client

def create_evaluation_dataset():
    """Create dataset with expected outputs"""
    client = Client()
    
    # Create dataset
    dataset_name = "graphrag_entity_extraction_eval"
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Test cases for entity extraction quality"
    )
    
    # Add test examples with expected outputs
    examples = [
        {
            "inputs": {
                "section_text": "CRISPR-Cas9 was developed by Jennifer Doudna and Emmanuelle Charpentier at UC Berkeley.",
                "section_title": "Gene Editing Technology"
            },
            "outputs": {
                "expected_entities": [
                    {"entity_name": "CRISPR-Cas9", "entity_type": "TECHNOLOGY"},
                    {"entity_name": "Jennifer Doudna", "entity_type": "PERSON"},
                    {"entity_name": "Emmanuelle Charpentier", "entity_type": "PERSON"},
                    {"entity_name": "UC Berkeley", "entity_type": "ORGANIZATION"}
                ]
            }
        },
        {
            "inputs": {
                "section_text": "The COVID-19 pandemic caused by SARS-CoV-2 virus affected millions worldwide.",
                "section_title": "Pandemic Overview"
            },
            "outputs": {
                "expected_entities": [
                    {"entity_name": "COVID-19", "entity_type": "DISEASE"},
                    {"entity_name": "SARS-CoV-2", "entity_type": "VIRUS"},
                    {"entity_name": "pandemic", "entity_type": "CONCEPT"}
                ]
            }
        },
        {
            "inputs": {
                "section_text": "Machine learning algorithms like neural networks and deep learning have revolutionized AI research.",
                "section_title": "AI Technologies"
            },
            "outputs": {
                "expected_entities": [
                    {"entity_name": "machine learning", "entity_type": "TECHNOLOGY"},
                    {"entity_name": "neural networks", "entity_type": "TECHNOLOGY"},
                    {"entity_name": "deep learning", "entity_type": "TECHNOLOGY"},
                    {"entity_name": "AI", "entity_type": "TECHNOLOGY"}
                ]
            }
        }
    ]
    
    for example in examples:
        client.create_example(
            inputs=example["inputs"],
            outputs=example["outputs"],
            dataset_id=dataset.id
        )
    
    print(f"Created dataset: {dataset_name}")
    print(f"View at: https://smith.langchain.com/datasets")

if __name__ == "__main__":
    create_evaluation_dataset()
