"""
Test multiple prompt variants to find best performing version
"""
import asyncio
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
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

async def test_prompt_variants():
    """Test different prompt formulations"""
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Use a model that supports temperature
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY
    )
    client = Client()
    
    # Variant 1: Current prompt
    prompt_v1 = ChatPromptTemplate.from_template(
        "Extract entities from: {text}"
    )
    
    # Variant 2: More specific instructions
    prompt_v2 = ChatPromptTemplate.from_template(
        "Extract named entities including people, organizations, technologies, and concepts from: {text}\n\nFormat as JSON."
    )
    
    # Variant 3: Few-shot examples
    prompt_v3 = ChatPromptTemplate.from_template(
        "Extract entities. Example:\nInput: 'Dr. Smith studied CRISPR at MIT'\nOutput: {{\"entities\": [{{\"name\": \"Dr. Smith\", \"type\": \"PERSON\"}}, {{\"name\": \"CRISPR\", \"type\": \"TECHNOLOGY\"}}, {{\"name\": \"MIT\", \"type\": \"ORGANIZATION\"}}]}}\n\nNow extract from: {text}"
    )
    
    test_text = "CRISPR-Cas9 was developed by Jennifer Doudna and Emmanuelle Charpentier at UC Berkeley."
    
    # Test each variant (automatically traced)
    for i, prompt in enumerate([prompt_v1, prompt_v2, prompt_v3], 1):
        chain = prompt | llm
        result = await chain.ainvoke({"text": test_text})
        print(f"Variant {i} result: {result}")
    
    print("Compare variants at: https://smith.langchain.com/")

if __name__ == "__main__":
    asyncio.run(test_prompt_variants())
