#!/usr/bin/env python3
"""
Gemini API Integration Example for SageWrite
Shows how to integrate Gemini models into your application using environment variables.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

class GeminiService:
    """Service class for integrating Gemini API into SageWrite."""
    
    def __init__(self):
        """Initialize the Gemini service with API key from environment."""
        self.api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Model configurations
        self.generative_model = "gemini-2.0-flash"  # Fast and stable
        self.embedding_model = "text-embedding-004"  # Fast embeddings
        
    def generate_content(self, prompt: str, model: str = None) -> str:
        """Generate content using Gemini generative model."""
        model_name = model or self.generative_model
        
        try:
            model_instance = genai.GenerativeModel(model_name)
            response = model_instance.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Error generating content with {model_name}: {str(e)}")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        try:
            embeddings = []
            for text in texts:
                embedding = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(embedding["embedding"])
            return embeddings
        except Exception as e:
            raise Exception(f"Error getting embeddings: {str(e)}")
    
    def analyze_document(self, content: str) -> Dict[str, Any]:
        """Analyze a document and extract key insights."""
        prompt = f"""
        Analyze the following document and provide:
        1. Main topics and themes
        2. Key entities mentioned
        3. Important relationships
        4. Summary in 2-3 sentences
        
        Document content:
        {content[:2000]}  # Limit to first 2000 chars
        """
        
        analysis = self.generate_content(prompt)
        
        return {
            "analysis": analysis,
            "model_used": self.generative_model,
            "content_length": len(content)
        }
    
    def answer_question(self, question: str, context: str = None) -> str:
        """Answer a question, optionally with context."""
        if context:
            prompt = f"""
            Based on the following context, answer the question:
            
            Context: {context}
            
            Question: {question}
            
            Provide a clear and concise answer.
            """
        else:
            prompt = f"Answer this question: {question}"
        
        return self.generate_content(prompt)

# Example usage
def main():
    """Example usage of the GeminiService."""
    try:
        # Initialize the service
        gemini = GeminiService()
        
        print("🚀 Gemini Service Integration Example")
        print("=" * 50)
        
        # Test 1: Simple content generation
        print("\n📝 Test 1: Content Generation")
        response = gemini.generate_content("Explain machine learning in simple terms.")
        print(f"Response: {response[:100]}...")
        
        # Test 2: Document analysis
        print("\n📊 Test 2: Document Analysis")
        sample_doc = """
        Artificial intelligence is transforming healthcare through machine learning algorithms 
        that can analyze medical images, predict patient outcomes, and assist in drug discovery. 
        These AI systems help doctors make more accurate diagnoses and provide personalized treatments.
        """
        analysis = gemini.analyze_document(sample_doc)
        print(f"Analysis: {analysis['analysis'][:150]}...")
        
        # Test 3: Question answering
        print("\n❓ Test 3: Question Answering")
        answer = gemini.answer_question(
            "What are the benefits of AI in healthcare?",
            context=sample_doc
        )
        print(f"Answer: {answer[:100]}...")
        
        # Test 4: Embeddings
        print("\n🔍 Test 4: Text Embeddings")
        texts = [
            "Machine learning algorithms",
            "Healthcare AI applications",
            "Medical image analysis"
        ]
        embeddings = gemini.get_embeddings(texts)
        print(f"Generated {len(embeddings)} embeddings")
        print(f"Embedding dimension: {len(embeddings[0])}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()

