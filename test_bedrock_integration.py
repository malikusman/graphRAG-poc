"""
Test script for AWS Bedrock integration

This script tests:
1. Provider initialization
2. LLM generation
3. Embedding generation
4. Integration with existing codebase
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file
load_dotenv(project_root / ".env")

from app.core.llm_provider import get_llm, get_llm_provider
from app.core.embedding_provider import get_embedding_provider
from langchain_core.messages import HumanMessage, SystemMessage


async def test_llm_provider():
    """Test LLM provider initialization and generation"""
    print("\n" + "="*60)
    print("Testing AWS Bedrock LLM Provider")
    print("="*60)
    
    try:
        # Get provider
        provider = get_llm_provider()
        print(f"✅ Provider initialized: {type(provider).__name__}")
        print(f"   Model: {provider.get_model_name()}")
        
        # Get LLM instance
        llm = get_llm(temperature=0.1)
        print(f"✅ LLM instance created: {type(llm).__name__}")
        
        # Test simple generation
        print("\nTesting simple message generation...")
        messages = [HumanMessage(content="What is 2+2? Respond with just the number.")]
        response = await llm.ainvoke(messages)
        print(f"✅ Response received: {response.content[:100]}...")
        
        # Test with system message
        print("\nTesting with system message...")
        messages = [
            SystemMessage(content="You are a helpful assistant that responds briefly."),
            HumanMessage(content="What is the capital of France?")
        ]
        response = await llm.ainvoke(messages)
        print(f"✅ Response with system message: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM provider: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_provider():
    """Test embedding provider initialization and generation"""
    print("\n" + "="*60)
    print("Testing AWS Bedrock Embedding Provider")
    print("="*60)
    
    try:
        # Get provider
        provider = get_embedding_provider()
        print(f"✅ Provider initialized: {type(provider).__name__}")
        print(f"   Model: {provider.get_model_name()}")
        print(f"   Dimensions: {provider.get_embedding_dimensions()}")
        
        # Test single embedding
        print("\nTesting single embedding...")
        text = "This is a test sentence for embedding generation."
        embedding = provider.generate_embedding(text)
        
        if embedding:
            print(f"✅ Single embedding generated: {len(embedding)} dimensions")
            print(f"   First 5 values: {embedding[:5]}")
        else:
            print("❌ Failed to generate embedding")
            return False
        
        # Test batch embeddings
        print("\nTesting batch embeddings...")
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        embeddings = provider.generate_embeddings_batch(texts)
        
        if embeddings and all(emb is not None for emb in embeddings):
            print(f"✅ Batch embeddings generated: {len(embeddings)} embeddings")
            print(f"   All embeddings have {len(embeddings[0])} dimensions")
        else:
            print("❌ Failed to generate batch embeddings")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing embedding provider: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_services():
    """Test integration with existing services"""
    print("\n" + "="*60)
    print("Testing Integration with Services")
    print("="*60)
    
    try:
        from app.services.embeddings import EmbeddingsService
        
        # Test embedding service
        print("\nTesting EmbeddingsService with Bedrock...")
        embedding_service = EmbeddingsService()
        
        text = "Test document for embedding service."
        embedding = embedding_service.generate_embedding(text)
        
        if embedding:
            print(f"✅ EmbeddingsService works: {len(embedding)} dimensions")
        else:
            print("❌ EmbeddingsService failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_environment():
    """Check if environment is properly configured"""
    print("\n" + "="*60)
    print("Checking Environment Configuration")
    print("="*60)
    
    required_vars = [
        "LLM_PROVIDER",
        "EMBEDDING_PROVIDER",
        "BEDROCK_REGION",
        "BEDROCK_MODEL_ID",
        "BEDROCK_EMBEDDING_MODEL_ID",
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var} not set")
        else:
            # Mask sensitive values
            if "KEY" in var or "CREDENTIALS" in var or "SECRET" in var:
                print(f"✅ {var} is set (hidden)")
            else:
                print(f"✅ {var} = {value}")
    
    # Check AWS credentials
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key and aws_secret_key:
        print("✅ AWS credentials provided via environment variables")
    else:
        # Check if credentials might be in ~/.aws/credentials or via IAM role
        aws_creds_file = Path.home() / ".aws" / "credentials"
        if aws_creds_file.exists():
            print(f"✅ AWS credentials file found: {aws_creds_file}")
        else:
            print("⚠️  AWS credentials not found in environment variables or ~/.aws/credentials")
            print("   Make sure you have AWS credentials configured via:")
            print("   - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
            print("   - IAM role (if running on EC2/Lambda)")
            print("   - ~/.aws/credentials file")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("\n✅ Environment check passed")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AWS Bedrock Integration Test Suite")
    print("="*60)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please configure your environment variables.")
        print("   See env.example for required variables.")
        sys.exit(1)
    
    # Run tests
    results = []
    
    # Test LLM provider
    results.append(await test_llm_provider())
    
    # Test embedding provider
    results.append(test_embedding_provider())
    
    # Test service integration
    results.append(test_integration_with_services())
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    if passed < total:
        print(f"❌ Failed: {total - passed}/{total}")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

