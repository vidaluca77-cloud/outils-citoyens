"""
Integration tests for API endpoints
"""
import pytest
import sys
import os
import json

# Add the api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

@pytest.mark.parametrize("tool_id,payload", [
    ("amendes", {
        "tool_id": "amendes",
        "fields": {
            "identite": {
                "nom": "Dupont",
                "prenom": "Jean",
                "adresse": "123 rue de la Paix, 75001 Paris"
            },
            "amende": {
                "numero": "123456789",
                "date": "2024-01-15",
                "montant": "90"
            },
            "motif_contestation": "Erreur de lieu"
        }
    }),
    ("loyers", {
        "tool_id": "loyers",
        "fields": {
            "identite": {
                "nom": "Martin",
                "prenom": "Marie",
                "adresse": "456 avenue des Champs, 75008 Paris"
            },
            "logement": {
                "adresse": "789 rue du Logement, 75010 Paris",
                "surface": "50",
                "loyer": "1200"
            },
            "probleme": "Loyer trop élevé"
        }
    }),
    ("caf", {
        "tool_id": "caf",
        "fields": {
            "identite": {
                "nom": "Durand",
                "prenom": "Pierre",
                "adresse": "321 boulevard de la République, 69001 Lyon"
            },
            "numero_allocataire": "1234567",
            "prestation": "RSA",
            "probleme": "Suspension injustifiée"
        }
    })
])
def test_generate_endpoints(tool_id, payload):
    """Test /generate endpoint with different tools"""
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check required keys are present
    assert "resume" in data
    assert "lettre" in data  
    assert "checklist" in data
    assert "mentions" in data
    
    # Check lettre structure
    lettre = data["lettre"]
    assert "destinataire_bloc" in lettre
    assert "objet" in lettre
    assert "corps" in lettre
    assert "pj" in lettre
    assert "signature" in lettre
    
    # Check types
    assert isinstance(data["resume"], list)
    assert isinstance(data["checklist"], list)
    assert isinstance(data["mentions"], str)
    assert isinstance(lettre["pj"], list)
    
    # Check that corps has 4 paragraphs
    paragraphs = [p.strip() for p in lettre["corps"].split('\n\n') if p.strip()]
    assert len(paragraphs) == 4, f"Expected 4 paragraphs but got {len(paragraphs)} for {tool_id}"

def test_generate_invalid_tool():
    """Test /generate with invalid tool_id"""
    response = client.post("/generate", json={
        "tool_id": "invalid_tool",
        "fields": {"test": "data"}
    })
    # Should return 400 for invalid tool_id
    assert response.status_code == 400

def test_generate_malicious_input():
    """Test /generate with malicious input"""
    response = client.post("/generate", json={
        "tool_id": "amendes",
        "fields": {
            "nom": "<script>alert('xss')</script>Jean",
            "description": "Test javascript:alert('hack') here"
        }
    })
    assert response.status_code == 200
    # The response should not contain the malicious scripts
    data = response.json()
    response_str = json.dumps(data)
    assert "<script>" not in response_str
    assert "javascript:" not in response_str

if __name__ == "__main__":
    pytest.main([__file__])