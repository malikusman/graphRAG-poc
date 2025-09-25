"""
Unit tests for Weight Heuristics in relationship extraction
"""

import pytest
import json
from app.prompts.map.relationship_extraction import load_prompt
from app.models.relationships import RelationshipType


class TestWeightHeuristicsPrompt:
    """Test the enhanced relationship extraction prompt with weight heuristics"""
    
    def test_prompt_structure(self):
        """Test that the prompt has the correct structure and components"""
        # Load the prompt
        prompt_data = load_prompt("relationship_extraction")
        
        # Check basic structure
        assert "system_prompt" in prompt_data
        assert "user_prompt" in prompt_data
        assert "temperature" in prompt_data
        assert "max_tokens" in prompt_data
        
        # Check enhanced components
        user_prompt = prompt_data["user_prompt"]
        assert "linguistic_analysis" in user_prompt
        assert "Linguistic Cue Detection Rules" in user_prompt
        assert "Context-Aware Scoring" in user_prompt
        assert "Strength Calculation Process" in user_prompt
        assert "Example Calculations" in user_prompt
    
    def test_linguistic_cue_rules(self):
        """Test that all linguistic cue rules are present"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check hedging language rules
        assert "Hedging Language (-0.15)" in user_prompt
        assert "may, might, could, possibly" in user_prompt
        assert "likely, potentially, presumably" in user_prompt
        
        # Check negation rules
        assert "Strong negation (-0.25)" in user_prompt
        assert "not, no, never, fails to" in user_prompt
        assert "Weak negation (-0.10)" in user_prompt
        assert "rarely, seldom, infrequently" in user_prompt
        
        # Check evidence strength rules
        assert "Strong evidence (+0.15)" in user_prompt
        assert "proven, confirmed, demonstrated" in user_prompt
        assert "Statistical significance (+0.10)" in user_prompt
        assert "p<0.05, p<0.01, significant" in user_prompt
        assert "Quantitative evidence (+0.05)" in user_prompt
        assert "specific numbers, percentages" in user_prompt
    
    def test_context_aware_scoring(self):
        """Test that context-aware scoring rules are present"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check context scoring rules
        assert "Methods section: +0.05" in user_prompt
        assert "Results section: +0.10" in user_prompt
        assert "Discussion/Conclusion: -0.05" in user_prompt
        assert "Introduction: -0.10" in user_prompt
    
    def test_strength_calculation_examples(self):
        """Test that strength calculation examples are present and correct"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check example calculations
        assert "Example 1:" in user_prompt
        assert "Example 2:" in user_prompt
        assert "Example 3:" in user_prompt
        
        # Check that examples show proper calculations
        assert "Base: 0.70" in user_prompt
        assert "Final: 0.95" in user_prompt
        assert "Final: 0.45" in user_prompt
        assert "Final: 0.90" in user_prompt
    
    def test_output_format(self):
        """Test that the output format includes linguistic analysis"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check output format includes linguistic analysis
        assert "linguistic_analysis" in user_prompt
        assert "Brief explanation of linguistic cues" in user_prompt
        
        # Check JSON structure includes new field
        assert '"linguistic_analysis":' in user_prompt
    
    def test_relationship_types_completeness(self):
        """Test that all relationship types are included"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check that all relationship types from enum are present
        for rel_type in RelationshipType:
            assert rel_type.value in user_prompt
        
        # Check specific new relationship types
        assert "targets" in user_prompt
        assert "cultured_in" in user_prompt
        assert "supplemented_with" in user_prompt
        assert "derived_from" in user_prompt
        assert "encoded_by" in user_prompt


class TestLinguisticCueDetection:
    """Test linguistic cue detection logic"""
    
    def test_hedging_detection(self):
        """Test detection of hedging language"""
        hedging_words = [
            "may", "might", "could", "possibly", "suggests", "indicates",
            "appears to", "seems to", "likely", "potentially", "presumably"
        ]
        
        # Test that prompt includes these hedging words
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        for word in hedging_words:
            assert word in user_prompt
    
    def test_negation_detection(self):
        """Test detection of negation language"""
        strong_negations = ["not", "no", "never", "fails to", "cannot", "unable to"]
        weak_negations = ["rarely", "seldom", "infrequently", "minimally", "slightly"]
        
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        for word in strong_negations + weak_negations:
            assert word in user_prompt
    
    def test_evidence_strength_detection(self):
        """Test detection of evidence strength indicators"""
        strong_evidence = ["proven", "confirmed", "demonstrated", "established", "validated"]
        statistical_evidence = ["p<0.05", "p<0.01", "significant", "highly significant"]
        quantitative_evidence = ["percentages", "fold changes", "concentrations", "measurements"]
        
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        for word in strong_evidence + statistical_evidence + quantitative_evidence:
            assert word in user_prompt


class TestStrengthCalculationLogic:
    """Test strength calculation logic and examples"""
    
    def test_base_strength(self):
        """Test that base strength is correctly set"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        assert "Start with base strength: 0.70" in user_prompt
    
    def test_adjustment_ranges(self):
        """Test that adjustment ranges are reasonable"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check that adjustments are within reasonable ranges
        assert "(-0.15)" in user_prompt  # Hedging
        assert "(-0.25)" in user_prompt  # Strong negation
        assert "(-0.10)" in user_prompt  # Weak negation/evidence
        assert "(+0.15)" in user_prompt  # Strong evidence
        assert "(+0.10)" in user_prompt  # Statistical significance
        assert "(+0.05)" in user_prompt  # Quantitative evidence
    
    def test_clamping_instruction(self):
        """Test that clamping instruction is present"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        assert "Clamp final value between 0.0 and 1.0" in user_prompt
    
    def test_compound_effects(self):
        """Test that compound effects are handled"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        assert "Compound Effects" in user_prompt
        assert "Multiple cues in same sentence" in user_prompt
        assert "Conflicting cues" in user_prompt


class TestPromptQuality:
    """Test overall prompt quality and completeness"""
    
    def test_prompt_length(self):
        """Test that prompt is comprehensive but not excessive"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check that prompt is substantial but reasonable
        assert len(user_prompt) > 2000  # Comprehensive
        assert len(user_prompt) < 10000  # Not excessive
    
    def test_instruction_clarity(self):
        """Test that instructions are clear and actionable"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check for clear step-by-step instructions
        assert "Strength Calculation Process:" in user_prompt
        assert "1. Start with base strength" in user_prompt
        assert "2. Identify all linguistic cues" in user_prompt
        assert "3. Apply cue adjustments" in user_prompt
    
    def test_example_quality(self):
        """Test that examples are realistic and educational"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check for realistic scientific examples
        assert "CRISPR-Cas9" in user_prompt
        assert "metformin" in user_prompt
        assert "TP53" in user_prompt
        assert "gene editing" in user_prompt
        assert "cancer" in user_prompt
    
    def test_json_format_validation(self):
        """Test that JSON format is properly specified"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check JSON structure
        assert "```json" in user_prompt
        assert "{{" in user_prompt  # Escaped braces
        assert "}}" in user_prompt  # Escaped braces
        assert '"relationships":' in user_prompt
        assert '"source_entity":' in user_prompt
        assert '"target_entity":' in user_prompt
        assert '"relationship_type":' in user_prompt
        assert '"relationship_strength":' in user_prompt
        assert '"description":' in user_prompt
        assert '"provenance":' in user_prompt
        assert '"linguistic_analysis":' in user_prompt


class TestPromptIntegration:
    """Test integration aspects of the prompt"""
    
    def test_temperature_setting(self):
        """Test that temperature is set appropriately for consistency"""
        prompt_data = load_prompt("relationship_extraction")
        
        assert prompt_data["temperature"] == 0.1  # Low temperature for consistency
    
    def test_max_tokens_setting(self):
        """Test that max_tokens is sufficient for detailed responses"""
        prompt_data = load_prompt("relationship_extraction")
        
        assert prompt_data["max_tokens"] == 3000  # Increased for detailed analysis
    
    def test_prompt_consistency(self):
        """Test that prompt is internally consistent"""
        prompt_data = load_prompt("relationship_extraction")
        user_prompt = prompt_data["user_prompt"]
        
        # Check that base strength is consistent
        assert user_prompt.count("0.70") >= 3  # Base strength mentioned multiple times
        
        # Check that adjustment values are consistent
        assert user_prompt.count("(-0.15)") >= 1  # Hedging adjustment
        assert user_prompt.count("(-0.25)") >= 1  # Strong negation
        assert user_prompt.count("(+0.15)") >= 1  # Strong evidence


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])

