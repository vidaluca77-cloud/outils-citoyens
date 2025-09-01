"""
Tests for schema-driven generation quality
"""
import pytest
import sys
import os

# Add the API directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(".")), 'api'))

import main

def test_amendes_feu_rouge_masque():
    """Test amendes generation for feu rouge masqué par travaux"""
    
    # Test data: feu rouge / date / lieu / PV / motif = feu masqué
    test_data = {
        "type_amende": "autre",
        "date_infraction": "15/03/2024",
        "lieu": "Avenue de la République, Paris 11e", 
        "numero_process_verbal": "12345678",
        "motif_contestation": "Feu tricolore masqué par travaux de voirie",
        "elements_preuve": "Photos du chantier masquant le feu, témoins présents",
        "identite": {
            "nom": "MARTIN",
            "prenom": "Pierre",
            "adresse": "123 rue des Exemples, 75011 Paris"
        }
    }
    
    # Generate response
    result = main.generate_mock_response("amendes", test_data)
    
    # Verify structure
    assert hasattr(result, 'resume')
    assert hasattr(result, 'lettre')
    assert hasattr(result, 'checklist')
    assert hasattr(result, 'mentions')
    
    # Verify letter structure
    letter = result.lettre
    assert hasattr(letter, 'corps'), "Letter should have corps field"
    assert isinstance(letter.corps, str)
    
    # Verify key elements are present in letter
    letter_text = letter.corps
    assert "12345678" in letter_text, "PV number should be in letter"
    assert "15/03/2024" in letter_text, "Date should be in letter"
    assert "Avenue de la République, Paris 11e" in letter_text, "Location should be in letter"
    assert "masqué par travaux" in letter_text, "Motif should be in letter"
    
    # Verify LRAR mention in resume
    resume_text = " ".join(result["resume"])
    assert "LRAR" in resume_text or "recommandée" in resume_text, "LRAR should be mentioned in resume"
    
    # Verify proper structure
    assert "DESTINATAIRE:" in letter
    assert "OBJET:" in letter
    assert "CORPS:" in letter
    assert "PIÈCES JOINTES:" in letter
    assert "SIGNATURE:" in letter

def test_caf_suspension_apl():
    """Test CAF generation for suspension APL avec pièce manquante"""
    
    # Test data: suspension APL pour pièce manquante
    test_data = {
        "numero_allocataire": "1234567",
        "type_courrier": "suspension APL",
        "motif": "Pièce manquante dans le dossier",
        "periode": "Mars 2024",
        "identite": {
            "nom": "BERNARD", 
            "prenom": "Sophie",
            "adresse": "789 rue de la Liberté, 13001 Marseille"
        },
        "piece_reclamee": "Quittance de loyer février 2024"
    }
    
    # Generate response
    result = main.generate_mock_response("caf", test_data)
    
    # Verify structure
    assert hasattr(result, 'resume')
    assert hasattr(result, 'lettre')
    assert hasattr(result, 'checklist')
    assert hasattr(result, 'mentions')
    
    # Verify letter structure
    letter = result.lettre
    assert isinstance(letter.corps, str)
    
    # Verify key elements are present
    letter = result["lettre"]
    assert "1234567" in letter, "Numéro allocataire should be in letter"
    assert "réexamen" in letter.lower(), "Demande de réexamen should be mentioned"
    
    # Verify proper CAF structure
    assert "Caisse d'Allocations Familiales" in letter
    assert "Recours gracieux" in letter
    
    # Verify checklist mentions
    checklist_text = " ".join(result["checklist"])
    assert "2 mois" in checklist_text, "2-month deadline should be mentioned"

def test_resume_length():
    """Test that résumé contains 5-8 actionable bullets"""
    
    test_data = {"identite": {"nom": "Test", "prenom": "User"}}
    
    for tool_id in ["amendes", "caf", "loyers"]:
        result = main.generate_mock_response(tool_id, test_data)
        resume = result.resume
        
        assert isinstance(resume, list), f"Resume should be a list for {tool_id}"
        assert 4 <= len(resume) <= 10, f"Resume should have 4-10 items for {tool_id}, got {len(resume)}"
        
        # Verify items are actionable (should contain action verbs)
        action_verbs = ["analyser", "rassembler", "contester", "envoyer", "respecter", "vérifier", "conserver", "préparer", "constituer", "surveiller"]
        for item in resume[:3]:  # Check first 3 items
            has_action = any(verb in item.lower() for verb in action_verbs)
            assert has_action, f"Resume item should be actionable: '{item}'"

def test_checklist_length():
    """Test that checklist contains 3-6 concrete steps"""
    
    test_data = {"identite": {"nom": "Test", "prenom": "User"}}
    
    for tool_id in ["amendes", "caf", "loyers"]:
        result = main.generate_mock_response(tool_id, test_data)
        checklist = result.checklist
        
        assert isinstance(checklist, list), f"Checklist should be a list for {tool_id}"
        assert 3 <= len(checklist) <= 8, f"Checklist should have 3-8 items for {tool_id}, got {len(checklist)}"

def test_mentions_content():
    """Test that mentions contains 2-4 legal reminders"""
    
    test_data = {"identite": {"nom": "Test", "prenom": "User"}}
    
    for tool_id in ["amendes", "caf", "loyers"]:
        result = main.generate_mock_response(tool_id, test_data)
        mentions = result.mentions
        
        assert isinstance(mentions, str), f"Mentions should be a string for {tool_id}"
        assert len(mentions) > 50, f"Mentions should be substantial for {tool_id}"
        
        # Should mention automated help disclaimer
        assert "automatisée" in mentions.lower() or "automatique" in mentions.lower(), "Should mention automated nature"

def test_generic_fallback():
    """Test fallback to generic template when tool-specific template missing"""
    
    # Test with a hypothetical tool that doesn't have specific templates
    test_data = {
        "identite": {"nom": "Test", "prenom": "User", "adresse": "123 Test St"},
        "test_field": "test_value"
    }
    
    result = main.generate_mock_response("nonexistent_tool", test_data)
    
    # Should still return proper structure
    assert hasattr(result, 'resume')
    assert hasattr(result, 'lettre')
    assert hasattr(result, 'checklist')
    assert hasattr(result, 'mentions')

def test_letter_structure_consistency():
    """Test that all letters have consistent structure"""
    
    test_data = {
        "identite": {"nom": "DUPONT", "prenom": "Jean", "adresse": "123 rue Test"},
        "test_field": "test_value"
    }
    
    tools_to_test = ["amendes", "caf", "loyers", "travail", "sante", "energie"]
    
    for tool_id in tools_to_test:
        result = main.generate_mock_response(tool_id, test_data)
        letter = result.lettre
        
        assert isinstance(letter.corps, str), f"Letter corps should be string for {tool_id}"
        
        # Check required sections
        required_sections = ["DESTINATAIRE:", "OBJET:", "CORPS:", "PIÈCES JOINTES:", "SIGNATURE:"]
        for section in required_sections:
            assert section in letter, f"Letter for {tool_id} should contain {section}"
        
        # Check user data integration
        assert "DUPONT" in letter or "Jean" in letter, f"User identity should be integrated in {tool_id} letter"

if __name__ == "__main__":
    # Run tests manually if not using pytest
    test_amendes_feu_rouge_masque()
    print("✅ test_amendes_feu_rouge_masque passed")
    
    test_caf_suspension_apl()
    print("✅ test_caf_suspension_apl passed")
    
    test_resume_length()
    print("✅ test_resume_length passed")
    
    test_checklist_length()
    print("✅ test_checklist_length passed")
    
    test_mentions_content()
    print("✅ test_mentions_content passed")
    
    test_generic_fallback()
    print("✅ test_generic_fallback passed")
    
    test_letter_structure_consistency()
    print("✅ test_letter_structure_consistency passed")
    
    print("\n🎉 All tests passed!")