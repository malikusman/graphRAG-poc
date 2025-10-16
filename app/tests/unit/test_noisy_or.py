"""
Unit tests for Noisy-OR mathematical calculations
"""

import pytest
from app.utils.math_utils import calculate_noisy_or_strength, calculate_weighted_average, clamp_value


class TestNoisyORCalculation:
    """Test cases for Noisy-OR strength calculation"""
    
    def test_single_strength(self):
        """Test Noisy-OR with single strength value"""
        # Single strength should return the same value
        assert calculate_noisy_or_strength([0.8]) == 0.8
        assert calculate_noisy_or_strength([0.5]) == 0.5
        assert calculate_noisy_or_strength([0.0]) == 0.0
        assert calculate_noisy_or_strength([1.0]) == 1.0
    
    def test_two_strengths(self):
        """Test Noisy-OR with two strength values"""
        # [0.8, 0.9] → 1 - (1-0.8) × (1-0.9) = 1 - 0.2 × 0.1 = 0.98
        result = calculate_noisy_or_strength([0.8, 0.9])
        assert abs(result - 0.98) < 0.001
        
        # [0.5, 0.6] → 1 - 0.5 × 0.4 = 1 - 0.2 = 0.8
        result = calculate_noisy_or_strength([0.5, 0.6])
        assert abs(result - 0.8) < 0.001
    
    def test_multiple_strengths(self):
        """Test Noisy-OR with multiple strength values"""
        # [0.5, 0.6, 0.7] → 1 - 0.5 × 0.4 × 0.3 = 1 - 0.06 = 0.94
        result = calculate_noisy_or_strength([0.5, 0.6, 0.7])
        assert abs(result - 0.94) < 0.001
        
        # [0.8, 0.9, 0.95] → 1 - 0.2 × 0.1 × 0.05 = 1 - 0.001 = 0.999
        result = calculate_noisy_or_strength([0.8, 0.9, 0.95])
        assert abs(result - 0.999) < 0.001
    
    def test_edge_cases(self):
        """Test Noisy-OR with edge case values"""
        # All zeros
        assert calculate_noisy_or_strength([0.0, 0.0, 0.0]) == 0.0
        
        # All ones (should be capped at 0.99)
        result = calculate_noisy_or_strength([1.0, 1.0, 1.0])
        assert result == 0.99  # Default cap
        
        # Mixed zeros and ones
        result = calculate_noisy_or_strength([0.0, 1.0, 0.0])
        assert abs(result - 1.0) < 0.001
    
    def test_invalid_strengths(self):
        """Test Noisy-OR with invalid strength values"""
        # Negative values should be filtered out
        result = calculate_noisy_or_strength([-0.1, 0.8, 0.9])
        assert abs(result - 0.98) < 0.001  # Should ignore -0.1
        
        # Values > 1.0 should be filtered out
        result = calculate_noisy_or_strength([0.8, 1.5, 0.9])
        assert abs(result - 0.98) < 0.001  # Should ignore 1.5
        
        # All invalid values
        assert calculate_noisy_or_strength([-0.1, 1.5, -0.5]) == 0.0
    
    def test_empty_list(self):
        """Test Noisy-OR with empty list"""
        assert calculate_noisy_or_strength([]) == 0.0
    
    def test_custom_cap(self):
        """Test Noisy-OR with custom cap value"""
        # Test with lower cap
        result = calculate_noisy_or_strength([0.8, 0.9, 0.95], cap_at=0.95)
        assert result == 0.95
        
        # Test with higher cap (should not affect normal values)
        result = calculate_noisy_or_strength([0.8, 0.9], cap_at=1.0)
        assert abs(result - 0.98) < 0.001
    
    def test_mathematical_verification(self):
        """Test Noisy-OR with known mathematical results"""
        test_cases = [
            # (input_strengths, expected_result, tolerance)
            ([0.2, 0.3], 0.44, 0.01),  # 1 - 0.8 × 0.7 = 0.44
            ([0.1, 0.2, 0.3], 0.496, 0.01),  # 1 - 0.9 × 0.8 × 0.7 = 0.496
            ([0.9, 0.95], 0.995, 0.001),  # 1 - 0.1 × 0.05 = 0.995
        ]
        
        for strengths, expected, tolerance in test_cases:
            result = calculate_noisy_or_strength(strengths)
            assert abs(result - expected) < tolerance, f"Expected {expected}, got {result} for {strengths}"


class TestWeightedAverage:
    """Test cases for weighted average calculation"""
    
    def test_equal_weights(self):
        """Test weighted average with equal weights"""
        values = [1.0, 2.0, 3.0, 4.0]
        weights = [1.0, 1.0, 1.0, 1.0]
        result = calculate_weighted_average(values, weights)
        assert result == 2.5  # (1+2+3+4)/4
    
    def test_unequal_weights(self):
        """Test weighted average with unequal weights"""
        values = [1.0, 2.0, 3.0]
        weights = [1.0, 2.0, 3.0]  # 2.0 should have double weight, 3.0 should have triple weight
        # (1×1 + 2×2 + 3×3) / (1+2+3) = (1+4+9)/6 = 14/6 ≈ 2.33
        result = calculate_weighted_average(values, weights)
        assert abs(result - 2.333) < 0.01
    
    def test_no_weights(self):
        """Test weighted average without weights (should use equal weights)"""
        values = [1.0, 2.0, 3.0, 4.0]
        result = calculate_weighted_average(values)
        assert result == 2.5  # Should be same as arithmetic mean
    
    def test_empty_values(self):
        """Test weighted average with empty values"""
        assert calculate_weighted_average([]) == 0.0
    
    def test_mismatched_lengths(self):
        """Test weighted average with mismatched value and weight lengths"""
        values = [1.0, 2.0]
        weights = [1.0, 2.0, 3.0]
        
        with pytest.raises(ValueError):
            calculate_weighted_average(values, weights)


class TestClampValue:
    """Test cases for value clamping"""
    
    def test_normal_values(self):
        """Test clamping with values within bounds"""
        assert clamp_value(0.5) == 0.5
        assert clamp_value(0.0) == 0.0
        assert clamp_value(1.0) == 1.0
    
    def test_values_below_min(self):
        """Test clamping with values below minimum"""
        assert clamp_value(-0.5) == 0.0
        assert clamp_value(-10.0) == 0.0
    
    def test_values_above_max(self):
        """Test clamping with values above maximum"""
        assert clamp_value(1.5) == 1.0
        assert clamp_value(10.0) == 1.0
    
    def test_custom_bounds(self):
        """Test clamping with custom bounds"""
        assert clamp_value(5.0, min_val=0.0, max_val=10.0) == 5.0
        assert clamp_value(-5.0, min_val=0.0, max_val=10.0) == 0.0
        assert clamp_value(15.0, min_val=0.0, max_val=10.0) == 10.0


class TestIntegration:
    """Integration tests for mathematical utilities"""
    
    def test_noisy_or_with_realistic_values(self):
        """Test Noisy-OR with realistic relationship strengths from scientific papers"""
        # Simulate relationship strengths from different sections of a paper
        section_strengths = [0.75, 0.82, 0.68, 0.91]  # Different confidence levels
        result = calculate_noisy_or_strength(section_strengths)
        
        # Should be high confidence due to multiple sources
        assert result > 0.95
        assert result <= 0.99  # Should be capped
    
    def test_noisy_or_with_hedged_claims(self):
        """Test Noisy-OR with hedged claims (lower confidence)"""
        # Simulate hedged claims with lower strengths
        hedged_strengths = [0.55, 0.62, 0.48]  # Lower due to hedging
        result = calculate_noisy_or_strength(hedged_strengths)
        
        # Should be moderate confidence
        assert 0.7 <= result <= 0.9
    
    def test_noisy_or_consistency(self):
        """Test that Noisy-OR is consistent across different orderings"""
        strengths1 = [0.8, 0.9, 0.7]
        strengths2 = [0.7, 0.8, 0.9]  # Same values, different order
        
        result1 = calculate_noisy_or_strength(strengths1)
        result2 = calculate_noisy_or_strength(strengths2)
        
        assert abs(result1 - result2) < 0.0001  # Should be identical


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
