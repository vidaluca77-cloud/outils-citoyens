"""
FastAPI router for legal search functionality
"""
import logging
import os
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, HTTPException
from openai import OpenAI

from .models import LegalQueryIn, LegalAnswer, LegalCitation
from .index import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter()

# OpenAI setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)


def format_citation(doc, index: int) -> LegalCitation:
    """Format a legal document as a citation"""
    return LegalCitation(
        title=doc.title,
        source=format_source_name(doc.source),
        date=doc.date.strftime("%d/%m/%Y"),
        url=doc.url,
        type=format_type_name(doc.type)
    )


def format_source_name(source: str) -> str:
    """Format source name for display"""
    source_names = {
        "legifrance": "Légifrance",
        "cour_cassation": "Cour de cassation",
        "conseil_etat": "Conseil d'État",
        "service_public": "Service-public.fr"
    }
    return source_names.get(source, source.title())


def format_type_name(type_: str) -> str:
    """Format document type for display"""
    type_names = {
        "code": "Code",
        "decret": "Décret",
        "decision": "Décision de justice",
        "fiche_pratique": "Fiche pratique"
    }
    return type_names.get(type_, type_.title())


def generate_legal_response(query: str, relevant_docs: List, citations: List[LegalCitation]) -> str:
    """Generate AI response with legal citations"""
    if not openai_client:
        # Fallback response when OpenAI is not available
        return f"""Je comprends votre question juridique concernant : "{query}".

Cependant, je ne peux pas fournir de réponse complète car le service d'IA n'est pas disponible actuellement. 

Voici les sources pertinentes que j'ai trouvées dans notre base de données juridiques récentes :

{chr(10).join([f"• {cite.title} ({cite.source}, {cite.date})" for cite in citations[:3]])}

Je vous recommande de consulter ces sources directement ou de contacter un professionnel du droit pour obtenir des conseils spécialisés."""

    # Prepare context from relevant documents
    context_parts = []
    for i, doc in enumerate(relevant_docs[:6], 1):
        context_parts.append(f"""
Source {i}: {doc.title} ({format_source_name(doc.source)}, {doc.date.strftime('%d/%m/%Y')})
URL: {doc.url}
Contenu: {doc.text[:800]}...
""")
    
    context = "\n".join(context_parts)
    
    # Citations for the prompt
    citations_text = "\n".join([
        f"[{i+1}] {cite.title} - {cite.source}, {cite.date} - {cite.url}"
        for i, cite in enumerate(citations)
    ])
    
    system_prompt = """Tu es un assistant juridique français expert. Tu dois répondre à des questions juridiques en te basant UNIQUEMENT sur les sources officielles récentes fournies.

RÈGLES STRICTES :
1. Réponds UNIQUEMENT en français dans un style administratif clair et accessible
2. Base-toi EXCLUSIVEMENT sur les sources fournies (ne pas inventer d'informations)
3. CITE obligatoirement au moins 3 sources pertinentes en utilisant la notation [1], [2], [3] dans ton texte
4. Sois précis sur les références légales (articles, dates, juridictions)
5. Adopte un ton professionnel mais accessible au grand public
6. N'émets JAMAIS d'avis juridique personnalisé - seulement des synthèses sourcées
7. Si les sources ne permettent pas de répondre complètement, le préciser clairement

FORMAT DE RÉPONSE :
- Introduction brève de la problématique
- Développement avec citations intégrées [1], [2], [3]
- Points clés à retenir
- Rappel des limites (pas d'avis personnalisé)"""

    user_prompt = f"""Question juridique : {query}

Sources récentes disponibles (< 24 mois) :
{context}

Citations à utiliser :
{citations_text}

Réponds en citant ces sources avec [1], [2], [3] etc. dans ton texte."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        # Fallback response
        return f"""Synthèse automatisée pour : "{query}"

Basé sur {len(relevant_docs)} sources officielles récentes, voici les éléments pertinents :

{chr(10).join([f"• {doc.title} ({format_source_name(doc.source)}, {doc.date.strftime('%d/%m/%Y')})" for doc in relevant_docs[:3]])}

Pour une analyse complète de votre situation, consultez directement ces sources ou un professionnel du droit."""


@router.post("/legal/search", response_model=LegalAnswer)
async def search_legal(query: LegalQueryIn):
    """Search legal documents and generate AI response"""
    try:
        # Input validation
        if not query.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if len(query.question) > 500:
            raise HTTPException(status_code=400, detail="Question too long (max 500 characters)")
        
        # Calculate date filter
        since_date = datetime.now() - timedelta(days=query.since_months * 30)
        
        # Get vector store and search
        vector_store = get_vector_store()
        results = await vector_store.search(
            query=query.question,
            k=query.limit * 2,  # Get more for better filtering
            since_date=since_date
        )
        
        if not results:
            return LegalAnswer(
                answer=f"Aucune source juridique pertinente trouvée dans les {query.since_months} derniers mois pour votre question : \"{query.question}\". Cela peut signifier que votre domaine juridique nécessite des sources plus spécialisées ou que les termes de recherche doivent être adaptés.",
                citations=[],
                disclaimer="Recherche automatisée dans les sources officielles récentes. En l'absence de résultats, consultez un professionnel du droit ou les bases de données juridiques spécialisées."
            )
        
        # Take best results and create citations
        best_results = results[:query.limit]
        citations = [format_citation(result.doc, i) for i, result in enumerate(best_results)]
        
        # Generate AI response
        answer = generate_legal_response(
            query.question,
            [result.doc for result in best_results],
            citations
        )
        
        return LegalAnswer(
            answer=answer,
            citations=citations,
            disclaimer="Synthèse automatisée à partir de sources officielles récentes. Ne constitue pas un avis juridique personnalisé. Consultez un avocat pour votre situation spécifique."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legal search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during legal search")


@router.get("/legal/health")
async def legal_health():
    """Health check for legal search service"""
    vector_store = get_vector_store()
    
    # Try a simple search to check if the system is working
    try:
        test_results = await vector_store.search("test", k=1)
        return {
            "status": "ok",
            "vector_store": type(vector_store).__name__,
            "openai_available": openai_client is not None,
            "test_search": len(test_results) >= 0
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "vector_store": type(vector_store).__name__,
            "openai_available": openai_client is not None
        }