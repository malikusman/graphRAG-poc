"""
Mathematical utility functions for GraphRAG processing
"""

from typing import List
import logging

logger = logging.getLogger(__name__)


def calculate_noisy_or_strength(strengths: List[float], cap_at: float = 0.99) -> float:
    """
    Calculate Noisy-OR strength: 1 - ∏(1 - strength_i)
    
    The Noisy-OR formula aggregates multiple independent pieces of evidence.
    It assumes that if any piece of evidence is true, the overall claim is more likely true.
    
    Mathematical formula: result = 1 - ∏(1 - strength_i)
    
    Examples:
        - [0.8] → 0.8
        - [0.8, 0.9] → 1 - (1-0.8) × (1-0.9) = 1 - 0.2 × 0.1 = 0.98
        - [0.5, 0.6, 0.7] → 1 - 0.5 × 0.4 × 0.3 = 1 - 0.06 = 0.94
    
    Args:
        strengths: List of strength values (0.0 to 1.0)
        cap_at: Maximum allowed strength (default 0.99 to avoid perfect confidence)
    
    Returns:
        Noisy-OR aggregated strength (0.0 to cap_at)
    """
    if not strengths:
        logger.warning("Empty strengths list provided to Noisy-OR calculation")
        return 0.0
    
    # Filter out invalid strengths and log warnings
    valid_strengths = []
    for strength in strengths:
        if 0.0 <= strength <= 1.0:
            valid_strengths.append(strength)
        else:
            logger.warning(f"Invalid strength value {strength} filtered out (must be 0.0-1.0)")
    
    if not valid_strengths:
        logger.warning("No valid strengths found in Noisy-OR calculation")
        return 0.0
    
    # Calculate noisy-OR: 1 - ∏(1 - strength_i)
    product = 1.0
    for strength in valid_strengths:
        product *= (1.0 - strength)
    
    result = 1.0 - product
    
    # Apply cap to avoid perfect confidence
    final_result = min(result, cap_at)
    
    logger.debug(f"Noisy-OR calculation: {valid_strengths} → {final_result:.4f}")
    
    return final_result


def calculate_weighted_average(values: List[float], weights: List[float] = None) -> float:
    """
    Calculate weighted average of values
    
    Args:
        values: List of values to average
        weights: Optional list of weights (defaults to equal weights)
    
    Returns:
        Weighted average
    """
    if not values:
        return 0.0
    
    if weights is None:
        return sum(values) / len(values)
    
    if len(values) != len(weights):
        raise ValueError("Values and weights must have the same length")
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    weight_sum = sum(weights)
    
    return weighted_sum / weight_sum if weight_sum > 0 else 0.0


def clamp_value(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp a value between min and max bounds
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))
