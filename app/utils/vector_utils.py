"""
Vector utility functions for semantic similarity calculations

This module provides functions for calculating similarity between vector embeddings
using NumPy for efficient computation.
"""

import numpy as np
import logging
from typing import List, Union, Optional

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: Union[List[float], np.ndarray], vec2: Union[List[float], np.ndarray]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Cosine similarity measures the cosine of the angle between two vectors,
    ranging from -1 (opposite) to 1 (identical). For embeddings, values typically
    range from 0 to 1.
    
    Formula: cos(θ) = (A · B) / (||A|| * ||B||)
    
    Where:
    - A · B is the dot product of vectors A and B
    - ||A|| is the L2 norm (magnitude) of vector A
    - ||B|| is the L2 norm (magnitude) of vector B
    
    Args:
        vec1: First vector (query embedding)
        vec2: Second vector (document embedding)
    
    Returns:
        Similarity score between -1 and 1 (typically 0 to 1 for embeddings)
        
    Example:
        >>> vec1 = [1.0, 2.0, 3.0]
        >>> vec2 = [1.0, 2.0, 3.0]
        >>> cosine_similarity(vec1, vec2)
        1.0  # Perfect match
        
        >>> vec3 = [1.0, 0.0]
        >>> vec4 = [0.0, 1.0]
        >>> cosine_similarity(vec3, vec4)
        0.0  # Orthogonal (unrelated)
    
    Notes:
        - This function is optimized for single pair comparisons
        - For batch comparisons, use batch_cosine_similarity() instead
        - Handles zero vectors gracefully (returns 0.0)
    """
    try:
        # Convert to numpy arrays if not already
        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        
        # Validate dimensions match
        if a.shape != b.shape:
            logger.error(f"Vector dimension mismatch: {a.shape} vs {b.shape}")
            return 0.0
        
        # Calculate dot product
        dot_product = np.dot(a, b)
        
        # Calculate L2 norms (magnitudes)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        # Handle zero vectors (avoid division by zero)
        if norm_a == 0 or norm_b == 0:
            logger.warning("Encountered zero vector in cosine similarity calculation")
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (norm_a * norm_b)
        
        # Ensure result is in valid range due to floating point precision
        similarity = np.clip(similarity, -1.0, 1.0)
        
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {str(e)}")
        return 0.0


def batch_cosine_similarity(
    query_vec: Union[List[float], np.ndarray],
    document_vecs: Union[List[List[float]], np.ndarray]
) -> np.ndarray:
    """
    Calculate cosine similarity between one query vector and multiple document vectors.
    
    This is an optimized vectorized implementation that's 10-100x faster than
    calling cosine_similarity() in a loop.
    
    Args:
        query_vec: Query embedding (1536 dimensions)
        document_vecs: Array of document embeddings (N x 1536)
    
    Returns:
        Array of similarity scores (N,) with values between -1 and 1
        
    Example:
        >>> query = [0.1, 0.2, 0.3]
        >>> docs = [
        ...     [0.1, 0.2, 0.3],  # Similar to query
        ...     [0.9, 0.8, 0.7],  # Different from query
        ...     [0.15, 0.25, 0.35]  # Very similar to query
        ... ]
        >>> scores = batch_cosine_similarity(query, docs)
        >>> scores
        array([1.0, 0.8, 0.99])  # Approximate scores
        
    Performance:
        - Single comparison: ~10-50 microseconds
        - Batch of 1000: ~1-5 milliseconds
        - Batch of 10000: ~10-50 milliseconds
        
    Notes:
        - Uses NumPy vectorization for speed
        - Memory efficient for large batches
        - Automatically handles zero vectors
    """
    try:
        # Convert to numpy arrays with appropriate dtypes
        query = np.array(query_vec, dtype=np.float32)
        documents = np.array(document_vecs, dtype=np.float32)
        
        # Validate dimensions
        if query.ndim != 1:
            logger.error(f"Query vector must be 1-dimensional, got shape {query.shape}")
            return np.zeros(len(document_vecs), dtype=np.float32)
        
        if documents.ndim != 2:
            logger.error(f"Document vectors must be 2-dimensional, got shape {documents.shape}")
            return np.zeros(len(document_vecs), dtype=np.float32)
        
        if query.shape[0] != documents.shape[1]:
            logger.error(f"Dimension mismatch: query {query.shape[0]} vs documents {documents.shape[1]}")
            return np.zeros(len(document_vecs), dtype=np.float32)
        
        # Calculate dot products for all documents at once (vectorized)
        # Shape: (N,) where N is number of documents
        dot_products = np.dot(documents, query)
        
        # Calculate L2 norms
        # Query norm: single scalar
        query_norm = np.linalg.norm(query)
        
        # Document norms: array of N values
        # axis=1 means calculate norm for each row (document)
        document_norms = np.linalg.norm(documents, axis=1)
        
        # Handle zero vectors
        if query_norm == 0:
            logger.warning("Query vector is zero")
            return np.zeros(len(document_vecs), dtype=np.float32)
        
        # Avoid division by zero for document norms
        # Replace zero norms with 1 (will result in 0 similarity)
        document_norms = np.where(document_norms == 0, 1.0, document_norms)
        
        # Calculate cosine similarities for all documents at once
        # Broadcasting: dot_products (N,) / (query_norm (scalar) * document_norms (N,))
        similarities = dot_products / (query_norm * document_norms)
        
        # Clip to valid range (handle floating point precision issues)
        similarities = np.clip(similarities, -1.0, 1.0)
        
        return similarities
        
    except Exception as e:
        logger.error(f"Error in batch cosine similarity: {str(e)}")
        return np.zeros(len(document_vecs), dtype=np.float32)


def normalize_vector(vec: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Normalize a vector to unit length (L2 norm = 1).
    
    This is useful for cosine similarity calculations since:
    cos(θ) = normalized_A · normalized_B
    
    A normalized vector has magnitude (L2 norm) of 1.0, which means
    the cosine similarity becomes simply the dot product.
    
    Args:
        vec: Input vector
    
    Returns:
        Normalized vector as numpy array
        
    Example:
        >>> vec = [3.0, 4.0]  # Magnitude = 5.0
        >>> normalized = normalize_vector(vec)
        >>> normalized
        array([0.6, 0.8])  # Magnitude = 1.0
        >>> np.linalg.norm(normalized)
        1.0
        
    Notes:
        - Returns zero vector if input is zero vector
        - Output is always float32 for memory efficiency
    """
    try:
        # Convert to numpy array
        vector = np.array(vec, dtype=np.float32)
        
        # Calculate L2 norm (magnitude)
        norm = np.linalg.norm(vector)
        
        # Handle zero vector
        if norm == 0:
            logger.warning("Cannot normalize zero vector")
            return vector
        
        # Normalize: divide by magnitude
        normalized = vector / norm
        
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing vector: {str(e)}")
        return np.array(vec, dtype=np.float32)


def euclidean_distance(vec1: Union[List[float], np.ndarray], vec2: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Euclidean (L2) distance between two vectors.
    
    Euclidean distance measures the straight-line distance between two points
    in vector space. Unlike cosine similarity, it considers magnitude.
    
    Formula: d(A, B) = √(Σ(ai - bi)²)
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Distance (0 = identical, larger = more different)
        
    Example:
        >>> vec1 = [1.0, 2.0, 3.0]
        >>> vec2 = [1.0, 2.0, 3.0]
        >>> euclidean_distance(vec1, vec2)
        0.0  # Identical
        
        >>> vec3 = [0.0, 0.0]
        >>> vec4 = [3.0, 4.0]
        >>> euclidean_distance(vec3, vec4)
        5.0  # Distance in 2D space
        
    Notes:
        - For embeddings, cosine similarity is usually preferred
        - Euclidean distance is sensitive to vector magnitude
        - Use this when magnitude matters (e.g., comparing counts)
    """
    try:
        # Convert to numpy arrays
        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        
        # Validate dimensions
        if a.shape != b.shape:
            logger.error(f"Vector dimension mismatch: {a.shape} vs {b.shape}")
            return float('inf')
        
        # Calculate Euclidean distance
        distance = np.linalg.norm(a - b)
        
        return float(distance)
        
    except Exception as e:
        logger.error(f"Error calculating Euclidean distance: {str(e)}")
        return float('inf')


def validate_embedding_dimensions(
    embedding: Union[List[float], np.ndarray],
    expected_dims: int = 1536
) -> bool:
    """
    Validate that an embedding has the expected number of dimensions.
    
    Args:
        embedding: Vector embedding to validate
        expected_dims: Expected number of dimensions (default: 1536 for text-embedding-3-small)
    
    Returns:
        True if valid, False otherwise
        
    Example:
        >>> embedding = [0.1] * 1536
        >>> validate_embedding_dimensions(embedding)
        True
        
        >>> wrong_embedding = [0.1] * 512
        >>> validate_embedding_dimensions(wrong_embedding)
        False
    """
    try:
        vec = np.array(embedding)
        
        # Check if 1-dimensional
        if vec.ndim != 1:
            logger.error(f"Embedding must be 1-dimensional, got {vec.ndim} dimensions")
            return False
        
        # Check dimension count
        if len(vec) != expected_dims:
            logger.error(f"Expected {expected_dims} dimensions, got {len(vec)}")
            return False
        
        # Check for NaN or Inf values
        if not np.isfinite(vec).all():
            logger.error("Embedding contains NaN or Inf values")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating embedding: {str(e)}")
        return False



