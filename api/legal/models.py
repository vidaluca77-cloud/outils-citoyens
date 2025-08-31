"""
Pydantic models for legal search functionality
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class LegalDoc(BaseModel):
    """Legal document representation for storage and retrieval"""
    title: str
    url: str
    source: str  # legifrance, cour_cassation, conseil_etat, service_public
    date: datetime
    type: str  # code, decret, decision, fiche_pratique, etc.
    jurisdiction: Optional[str] = None  # For court decisions
    text: str
    

class LegalQueryIn(BaseModel):
    """Input model for legal search queries"""
    question: str = Field(..., description="Question juridique de l'utilisateur")
    limit: int = Field(6, ge=1, le=20, description="Nombre maximum de documents à récupérer")
    since_months: int = Field(24, ge=1, le=36, description="Recherche sur les X derniers mois")
    

class LegalCitation(BaseModel):
    """Citation model for legal sources"""
    title: str
    source: str
    date: str  # Format: "DD/MM/YYYY"
    url: str
    type: str
    

class LegalAnswer(BaseModel):
    """Response model for legal search results"""
    answer: str = Field(..., description="Synthèse juridique en français avec citations")
    citations: List[LegalCitation] = Field(..., description="Liste des sources citées")
    disclaimer: str = Field(
        default="Synthèse automatisée à partir de sources officielles récentes. Ne constitue pas un avis juridique personnalisé.",
        description="Avertissement légal"
    )


class VectorSearchResult(BaseModel):
    """Internal model for vector search results"""
    doc: LegalDoc
    score: float
    relevance: float  # Combined score + freshness