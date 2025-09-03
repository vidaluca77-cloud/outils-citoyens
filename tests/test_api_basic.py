"""
Basic tests for API functionality
"""
import pytest
import sys
import os
import re

# Add the api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from main import ensure_four_paragraphs, GenerateRequest

def test_ensure_four_paragraphs_less_than_four():
    """Test ensure_four_paragraphs when input has fewer than 4 paragraphs"""
    # Test with 1 paragraph
    corps_1 = "Premier paragraphe."
    result = ensure_four_paragraphs(corps_1)
    paragraphs = result.split('\n\n')
    assert len(paragraphs) == 4
    assert paragraphs[0] == "Premier paragraphe."
    assert "Je vous expose ci-dessous" in paragraphs[1]
    
    # Test with 2 paragraphs
    corps_2 = "Premier paragraphe.\n\nSecond paragraphe."
    result = ensure_four_paragraphs(corps_2)
    paragraphs = result.split('\n\n')
    assert len(paragraphs) == 4
    assert paragraphs[0] == "Premier paragraphe."
    assert paragraphs[1] == "Second paragraphe."
    
    # Test with 3 paragraphs
    corps_3 = "Un.\n\nDeux.\n\nTrois."
    result = ensure_four_paragraphs(corps_3)
    paragraphs = result.split('\n\n')
    assert len(paragraphs) == 4

def test_ensure_four_paragraphs_more_than_four():
    """Test ensure_four_paragraphs when input has more than 4 paragraphs"""
    corps_5 = "Un.\n\nDeux.\n\nTrois.\n\nQuatre.\n\nCinq."
    result = ensure_four_paragraphs(corps_5)
    paragraphs = result.split('\n\n')
    assert len(paragraphs) == 4
    assert paragraphs[0] == "Un."
    assert paragraphs[1] == "Deux."
    assert paragraphs[2] == "Trois."
    assert "Quatre. Cinq." in paragraphs[3]  # Last paragraphs merged

def test_ensure_four_paragraphs_exactly_four():
    """Test ensure_four_paragraphs when input has exactly 4 paragraphs"""
    corps_4 = "Un.\n\nDeux.\n\nTrois.\n\nQuatre."
    result = ensure_four_paragraphs(corps_4)
    paragraphs = result.split('\n\n')
    assert len(paragraphs) == 4
    assert result == corps_4

def test_sanitizer_scripts():
    """Test sanitizer removes script tags and javascript"""
    test_request = GenerateRequest(
        tool_id="test",
        fields={
            "test_field": "Hello <script>alert('hack')</script> world",
            "js_field": "Click javascript:alert('xss') here"
        }
    )
    
    # Check that script tags are removed
    assert "<script>" not in test_request.fields["test_field"]
    assert "alert('hack')" not in test_request.fields["test_field"]
    assert "Hello  world" in test_request.fields["test_field"]
    
    # Check that javascript: is removed  
    assert "javascript:" not in test_request.fields["js_field"]
    assert "Click alert('xss') here" in test_request.fields["js_field"]

def test_sanitizer_length_limit():
    """Test sanitizer limits string length"""
    long_string = "a" * 6000  # Longer than 5000 char limit
    test_request = GenerateRequest(
        tool_id="test",
        fields={"long_field": long_string}
    )
    
    assert len(test_request.fields["long_field"]) <= 5000

if __name__ == "__main__":
    pytest.main([__file__])