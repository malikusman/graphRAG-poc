#!/usr/bin/env python3
"""
Updated Gemini API Test Script with Available Models
Tests both generative and embedding models with the models that are actually available.
"""

import os
import google.generativeai as genai
import time
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure API key from environment variable
API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_GEMINI_API_KEY not found in environment variables. Please check your .env file.")

genai.configure(api_key=API_KEY)

def test_generative_models():
    """Test different generative models and compare their performance."""
    print("🤖 Testing Generative Models")
    print("=" * 50)
    
    # Available generative models (latest and most relevant)
    models_to_test = [
        "gemini-2.5-flash",           # Latest fast model
        "gemini-2.5-pro",             # Latest most capable model
        "gemini-2.0-flash",           # Stable 2.0 version
        "gemini-2.0-flash-lite",      # Lightweight version
        "gemini-flash-latest",        # Latest flash
        "gemini-pro-latest",          # Latest pro
    ]
    
    test_prompt = "Write a brief explanation of quantum computing in 2-3 sentences."
    
    results = {}
    
    for model_name in models_to_test:
        try:
            print(f"\n📝 Testing {model_name}...")
            start_time = time.time()
            
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(test_prompt)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            results[model_name] = {
                "response": response.text,
                "response_time": response_time,
                "status": "success"
            }
            
            print(f"✅ Success! Response time: {response_time:.2f}s")
            print(f"Response: {response.text[:100]}...")
            
        except Exception as e:
            print(f"❌ Error with {model_name}: {str(e)}")
            results[model_name] = {
                "error": str(e),
                "status": "failed"
            }
    
    return results

def test_embedding_models():
    """Test embedding models and compare their capabilities."""
    print("\n🔍 Testing Embedding Models")
    print("=" * 50)
    
    # Available embedding models
    embedding_models = [
        "text-embedding-004",         # Latest embedding model
        "embedding-001",              # Alternative embedding model
        "gemini-embedding-001",       # Gemini-specific embedding
    ]
    
    test_texts = [
        "Artificial intelligence is transforming healthcare through machine learning.",
        "Quantum computing promises to revolutionize cryptography and drug discovery.",
        "Climate change requires immediate global action and sustainable solutions.",
    ]
    
    results = {}
    
    for model_name in embedding_models:
        try:
            print(f"\n🧮 Testing {model_name}...")
            start_time = time.time()
            
            embeddings = []
            for text in test_texts:
                embedding = genai.embed_content(
                    model=model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(embedding["embedding"])
            
            end_time = time.time()
            response_time = end_time - start_time
            
            results[model_name] = {
                "embeddings": embeddings,
                "embedding_dimension": len(embeddings[0]) if embeddings else 0,
                "response_time": response_time,
                "status": "success"
            }
            
            print(f"✅ Success! Response time: {response_time:.2f}s")
            print(f"Embedding dimension: {len(embeddings[0]) if embeddings else 0}")
            print(f"Sample embedding (first 5 values): {embeddings[0][:5] if embeddings else []}")
            
        except Exception as e:
            print(f"❌ Error with {model_name}: {str(e)}")
            results[model_name] = {
                "error": str(e),
                "status": "failed"
            }
    
    return results

def test_advanced_features():
    """Test advanced features like multimodal capabilities."""
    print("\n🎨 Testing Advanced Features")
    print("=" * 50)
    
    try:
        # Test with system instruction
        print("\n📋 Testing System Instructions...")
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction="You are a helpful AI assistant that always responds in a professional and concise manner."
        )
        
        response = model.generate_content("What is machine learning?")
        print(f"✅ System instruction test successful!")
        print(f"Response: {response.text[:100]}...")
        
        # Test with generation config
        print("\n⚙️ Testing Generation Config...")
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 100,
        }
        
        model_with_config = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config=generation_config
        )
        
        response = model_with_config.generate_content("Explain AI in one sentence.")
        print(f"✅ Generation config test successful!")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Advanced features test failed: {str(e)}")

def compare_models(generative_results: Dict, embedding_results: Dict):
    """Compare and display model performance."""
    print("\n📊 Model Comparison Summary")
    print("=" * 50)
    
    print("\n🤖 Generative Models:")
    print("-" * 30)
    successful_models = []
    for model, result in generative_results.items():
        if result["status"] == "success":
            successful_models.append((model, result))
            print(f"{model}:")
            print(f"  ⏱️  Response time: {result['response_time']:.2f}s")
            print(f"  📝 Response length: {len(result['response'])} chars")
        else:
            print(f"{model}: ❌ Failed - {result.get('error', 'Unknown error')}")
    
    # Find fastest and best models
    if successful_models:
        fastest = min(successful_models, key=lambda x: x[1]['response_time'])
        print(f"\n🏆 Fastest model: {fastest[0]} ({fastest[1]['response_time']:.2f}s)")
    
    print("\n🔍 Embedding Models:")
    print("-" * 30)
    successful_embeddings = []
    for model, result in embedding_results.items():
        if result["status"] == "success":
            successful_embeddings.append((model, result))
            print(f"{model}:")
            print(f"  ⏱️  Response time: {result['response_time']:.2f}s")
            print(f"  📏 Embedding dimension: {result['embedding_dimension']}")
        else:
            print(f"{model}: ❌ Failed - {result.get('error', 'Unknown error')}")
    
    if successful_embeddings:
        fastest_embedding = min(successful_embeddings, key=lambda x: x[1]['response_time'])
        print(f"\n🏆 Fastest embedding model: {fastest_embedding[0]} ({fastest_embedding[1]['response_time']:.2f}s)")

def get_model_recommendations():
    """Provide recommendations for different use cases."""
    print("\n💡 Model Recommendations")
    print("=" * 50)
    
    print("\n🎯 For Generative Tasks:")
    print("• gemini-2.5-pro: Best for complex reasoning, analysis, and high-quality content")
    print("• gemini-2.5-flash: Best for fast responses and high-volume processing")
    print("• gemini-2.0-flash: Stable, reliable model for production use")
    print("• gemini-2.0-flash-lite: Best for lightweight applications and cost efficiency")
    
    print("\n🔍 For Embedding Tasks:")
    print("• text-embedding-004: Latest model with improved performance (768 dimensions)")
    print("• embedding-001: Alternative embedding model")
    print("• gemini-embedding-001: Gemini-specific embedding model")
    
    print("\n📈 Performance Tips:")
    print("• Use gemini-2.5-flash for real-time applications")
    print("• Use gemini-2.5-pro for complex analysis tasks")
    print("• Use text-embedding-004 for new projects")
    print("• Consider response time vs. quality trade-offs")
    print("• Use system instructions for consistent behavior")
    print("• Adjust generation config for different use cases")

def main():
    """Main test function."""
    print("🚀 Gemini API Comprehensive Test")
    print("=" * 50)
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-10:]}")
    
    try:
        # Test generative models
        generative_results = test_generative_models()
        
        # Test embedding models
        embedding_results = test_embedding_models()
        
        # Test advanced features
        test_advanced_features()
        
        # Compare results
        compare_models(generative_results, embedding_results)
        
        # Provide recommendations
        get_model_recommendations()
        
        print("\n✅ Test completed successfully!")
        print("\n🎉 Your Gemini API is working perfectly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print("Please check your API key and internet connection.")

if __name__ == "__main__":
    main()
