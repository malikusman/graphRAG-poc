"""
Unit tests for vector utility functions

Tests cover:
- Cosine similarity calculations (single and batch)
- Vector normalization
- Euclidean distance
- Edge cases (zero vectors, mismatched dimensions)
- Performance validation
"""

import pytest
import numpy as np
import time
from app.utils.vector_utils import (
    cosine_similarity,
    batch_cosine_similarity,
    normalize_vector,
    euclidean_distance,
    validate_embedding_dimensions
)


class TestCosineSimilarity:
    """Test cosine similarity calculations"""
    
    def test_identical_vectors(self):
        """Test that identical vectors have similarity of 1.0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == pytest.approx(1.0, abs=1e-6)
        print("✓ Identical vectors test passed: similarity = 1.0")
    
    def test_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity of 0.0"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == pytest.approx(0.0, abs=1e-6)
        print("✓ Orthogonal vectors test passed: similarity = 0.0")
    
    def test_opposite_vectors(self):
        """Test that opposite vectors have similarity of -1.0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == pytest.approx(-1.0, abs=1e-6)
        print("✓ Opposite vectors test passed: similarity = -1.0")
    
    def test_similar_vectors(self):
        """Test vectors with high similarity"""
        vec1 = [0.1, 0.2, 0.3]
        vec2 = [0.15, 0.25, 0.35]
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Should be very similar (close to 1.0)
        assert similarity > 0.99
        print(f"✓ Similar vectors test passed: similarity = {similarity:.4f}")
    
    def test_zero_vector(self):
        """Test that zero vectors return 0.0 similarity"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0
        print("✓ Zero vector test passed: similarity = 0.0")
    
    def test_numpy_arrays(self):
        """Test that numpy arrays work as input"""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == pytest.approx(1.0, abs=1e-6)
        print("✓ NumPy arrays test passed")
    
    def test_dimension_mismatch(self):
        """Test that mismatched dimensions return 0.0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        
        similarity = cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0
        print("✓ Dimension mismatch test passed")
    
    def test_realistic_embeddings(self):
        """Test with realistic embedding-like vectors (1536 dimensions)"""
        # Generate random embeddings similar to OpenAI's
        np.random.seed(42)
        vec1 = np.random.randn(1536).astype(np.float32)
        vec2 = vec1 + np.random.randn(1536).astype(np.float32) * 0.1  # Similar but not identical
        
        similarity = cosine_similarity(vec1, vec2)
        
        # Should be high similarity (>0.9) since vec2 is based on vec1
        assert 0.9 < similarity < 1.0
        print(f"✓ Realistic embeddings test passed: similarity = {similarity:.4f}")


class TestBatchCosineSimilarity:
    """Test batch cosine similarity calculations"""
    
    def test_batch_single_document(self):
        """Test batch calculation with single document"""
        query = [1.0, 2.0, 3.0]
        docs = [[1.0, 2.0, 3.0]]
        
        similarities = batch_cosine_similarity(query, docs)
        
        assert len(similarities) == 1
        assert similarities[0] == pytest.approx(1.0, abs=1e-6)
        print("✓ Batch single document test passed")
    
    def test_batch_multiple_documents(self):
        """Test batch calculation with multiple documents"""
        query = [1.0, 2.0, 3.0]
        docs = [
            [1.0, 2.0, 3.0],     # Identical
            [0.0, 1.0, 0.0],     # Orthogonal-ish
            [2.0, 4.0, 6.0],     # Same direction, different magnitude
            [-1.0, -2.0, -3.0]   # Opposite
        ]
        
        similarities = batch_cosine_similarity(query, docs)
        
        assert len(similarities) == 4
        assert similarities[0] == pytest.approx(1.0, abs=1e-6)   # Identical
        assert similarities[2] == pytest.approx(1.0, abs=1e-6)   # Same direction
        assert similarities[3] == pytest.approx(-1.0, abs=1e-6)  # Opposite
        print(f"✓ Batch multiple documents test passed: scores = {similarities}")
    
    def test_batch_performance(self):
        """Test that batch is faster than loop"""
        # Generate realistic test data
        np.random.seed(42)
        query = np.random.randn(1536).astype(np.float32)
        docs = np.random.randn(1000, 1536).astype(np.float32)
        
        # Batch approach
        start_batch = time.time()
        batch_results = batch_cosine_similarity(query, docs)
        time_batch = time.time() - start_batch
        
        # Loop approach (test first 100 for speed)
        start_loop = time.time()
        loop_results = [cosine_similarity(query, doc) for doc in docs[:100]]
        time_loop = time.time() - start_loop
        
        # Extrapolate loop time to 1000
        time_loop_extrapolated = time_loop * 10
        
        print(f"✓ Batch performance test:")
        print(f"  - Batch (1000 docs): {time_batch*1000:.2f}ms")
        print(f"  - Loop (1000 docs, extrapolated): {time_loop_extrapolated*1000:.2f}ms")
        speedup = time_loop_extrapolated / time_batch if time_batch > 0 else 1
        print(f"  - Speedup: {speedup:.1f}x")
        
        # Just verify batch completes in reasonable time (< 100ms for 1000 docs)
        assert time_batch < 0.1, f"Batch too slow: {time_batch*1000:.2f}ms"
    
    def test_batch_zero_vectors(self):
        """Test batch with zero vectors"""
        query = [1.0, 2.0, 3.0]
        docs = [
            [0.0, 0.0, 0.0],  # Zero vector
            [1.0, 2.0, 3.0],  # Normal
        ]
        
        similarities = batch_cosine_similarity(query, docs)
        
        assert similarities[0] == 0.0  # Zero vector
        assert similarities[1] == pytest.approx(1.0, abs=1e-6)  # Normal
        print("✓ Batch zero vectors test passed")
    
    def test_batch_dimension_mismatch(self):
        """Test batch with mismatched dimensions"""
        query = [1.0, 2.0, 3.0]
        docs = [[1.0, 2.0]]  # Wrong dimension
        
        similarities = batch_cosine_similarity(query, docs)
        
        # Should return array of zeros
        assert all(s == 0.0 for s in similarities)
        print("✓ Batch dimension mismatch test passed")


class TestNormalizeVector:
    """Test vector normalization"""
    
    def test_normalize_simple(self):
        """Test normalization of simple vector"""
        vec = [3.0, 4.0]  # Magnitude = 5.0
        
        normalized = normalize_vector(vec)
        
        # Check values
        assert normalized[0] == pytest.approx(0.6, abs=1e-6)
        assert normalized[1] == pytest.approx(0.8, abs=1e-6)
        
        # Check magnitude = 1.0
        magnitude = np.linalg.norm(normalized)
        assert magnitude == pytest.approx(1.0, abs=1e-6)
        
        print(f"✓ Normalize simple test passed: {vec} → {normalized.tolist()}")
    
    def test_normalize_already_normalized(self):
        """Test normalizing an already normalized vector"""
        vec = [0.6, 0.8]  # Already normalized
        
        normalized = normalize_vector(vec)
        
        assert normalized[0] == pytest.approx(0.6, abs=1e-6)
        assert normalized[1] == pytest.approx(0.8, abs=1e-6)
        print("✓ Normalize already normalized test passed")
    
    def test_normalize_zero_vector(self):
        """Test normalizing zero vector"""
        vec = [0.0, 0.0, 0.0]
        
        normalized = normalize_vector(vec)
        
        # Should return zero vector unchanged
        assert all(v == 0.0 for v in normalized)
        print("✓ Normalize zero vector test passed")
    
    def test_normalized_cosine_similarity(self):
        """Test that normalized vectors simplify cosine similarity to dot product"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [2.0, 3.0, 4.0]
        
        # Normalize both
        norm1 = normalize_vector(vec1)
        norm2 = normalize_vector(vec2)
        
        # Cosine similarity should equal dot product for normalized vectors
        cosine_sim = cosine_similarity(vec1, vec2)
        dot_product = np.dot(norm1, norm2)
        
        assert cosine_sim == pytest.approx(dot_product, abs=1e-6)
        print("✓ Normalized cosine similarity test passed")


class TestEuclideanDistance:
    """Test Euclidean distance calculations"""
    
    def test_identical_vectors_distance(self):
        """Test distance between identical vectors is 0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        
        distance = euclidean_distance(vec1, vec2)
        
        assert distance == pytest.approx(0.0, abs=1e-6)
        print("✓ Identical vectors distance test passed: distance = 0.0")
    
    def test_simple_distance(self):
        """Test simple distance calculation"""
        vec1 = [0.0, 0.0]
        vec2 = [3.0, 4.0]
        
        distance = euclidean_distance(vec1, vec2)
        
        # Distance should be 5.0 (3-4-5 triangle)
        assert distance == pytest.approx(5.0, abs=1e-6)
        print("✓ Simple distance test passed: distance = 5.0")
    
    def test_distance_dimension_mismatch(self):
        """Test distance with mismatched dimensions"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        
        distance = euclidean_distance(vec1, vec2)
        
        # Should return infinity
        assert distance == float('inf')
        print("✓ Distance dimension mismatch test passed")


class TestValidateEmbeddingDimensions:
    """Test embedding validation"""
    
    def test_valid_embedding(self):
        """Test validation of correct embedding"""
        embedding = [0.1] * 1536
        
        is_valid = validate_embedding_dimensions(embedding)
        
        assert is_valid is True
        print("✓ Valid embedding test passed")
    
    def test_wrong_dimensions(self):
        """Test validation with wrong dimensions"""
        embedding = [0.1] * 512  # Wrong size
        
        is_valid = validate_embedding_dimensions(embedding)
        
        assert is_valid is False
        print("✓ Wrong dimensions test passed")
    
    def test_multidimensional_array(self):
        """Test validation with multidimensional array"""
        embedding = [[0.1] * 1536]  # 2D instead of 1D
        
        is_valid = validate_embedding_dimensions(embedding)
        
        assert is_valid is False
        print("✓ Multidimensional array test passed")
    
    def test_nan_values(self):
        """Test validation with NaN values"""
        embedding = [0.1] * 1536
        embedding[100] = float('nan')
        
        is_valid = validate_embedding_dimensions(embedding)
        
        assert is_valid is False
        print("✓ NaN values test passed")
    
    def test_custom_dimensions(self):
        """Test validation with custom expected dimensions"""
        embedding = [0.1] * 3072  # text-embedding-3-large size
        
        is_valid = validate_embedding_dimensions(embedding, expected_dims=3072)
        
        assert is_valid is True
        print("✓ Custom dimensions test passed")


def run_all_tests():
    """Run all tests and print summary"""
    print("\n" + "="*70)
    print("VECTOR UTILS TEST SUITE")
    print("="*70 + "\n")
    
    # Run pytest programmatically
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()

