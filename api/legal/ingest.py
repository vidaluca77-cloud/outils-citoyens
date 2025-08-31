"""
Legal data ingestion from French public sources
"""
import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
import time

from .models import LegalDoc
from .index import get_vector_store

logger = logging.getLogger(__name__)


class LegalDataIngester:
    """Main class for legal data ingestion"""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Outils-Citoyens/1.0 (Legal Research Tool)'
        })
    
    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                last_sentence = text.rfind('.', start, end)
                if last_sentence > start + chunk_size // 2:
                    end = last_sentence + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    async def ingest_all_recent(self, start_date: datetime) -> Dict[str, int]:
        """Ingest from all available sources"""
        results = {
            'legifrance': 0,
            'cour_cassation': 0,
            'conseil_etat': 0,
            'service_public': 0,
            'total': 0
        }
        
        logger.info(f"Starting legal data ingestion from {start_date}")
        
        # Fetch from each source
        docs = []
        
        # Légifrance
        try:
            legifrance_docs = await self.fetch_legifrance_recent(start_date)
            docs.extend(legifrance_docs)
            results['legifrance'] = len(legifrance_docs)
            logger.info(f"Retrieved {len(legifrance_docs)} documents from Légifrance")
        except Exception as e:
            logger.error(f"Error fetching Légifrance data: {e}")
        
        # Cour de cassation
        try:
            cassation_docs = await self.fetch_cour_de_cassation_recent(start_date)
            docs.extend(cassation_docs)
            results['cour_cassation'] = len(cassation_docs)
            logger.info(f"Retrieved {len(cassation_docs)} documents from Cour de cassation")
        except Exception as e:
            logger.error(f"Error fetching Cour de cassation data: {e}")
        
        # Conseil d'État
        try:
            conseil_docs = await self.fetch_conseil_etat_recent(start_date)
            docs.extend(conseil_docs)
            results['conseil_etat'] = len(conseil_docs)
            logger.info(f"Retrieved {len(conseil_docs)} documents from Conseil d'État")
        except Exception as e:
            logger.error(f"Error fetching Conseil d'État data: {e}")
        
        # Service-public.fr
        try:
            service_docs = await self.fetch_service_public_recent(start_date)
            docs.extend(service_docs)
            results['service_public'] = len(service_docs)
            logger.info(f"Retrieved {len(service_docs)} documents from Service-public.fr")
        except Exception as e:
            logger.error(f"Error fetching Service-public.fr data: {e}")
        
        # Process and chunk documents
        all_chunks = []
        for doc in docs:
            chunks = self.chunk_text(doc.text)
            for i, chunk in enumerate(chunks):
                chunk_doc = LegalDoc(
                    title=f"{doc.title} (partie {i+1}/{len(chunks)})" if len(chunks) > 1 else doc.title,
                    url=doc.url,
                    source=doc.source,
                    date=doc.date,
                    type=doc.type,
                    jurisdiction=doc.jurisdiction,
                    text=chunk
                )
                all_chunks.append(chunk_doc)
        
        # Store in vector database
        if all_chunks:
            success = await self.vector_store.upsert(all_chunks)
            if success:
                results['total'] = len(all_chunks)
                logger.info(f"Successfully stored {len(all_chunks)} document chunks")
            else:
                logger.error("Failed to store documents in vector store")
        
        return results
    
    async def fetch_legifrance_recent(self, start_date: datetime) -> List[LegalDoc]:
        """Fetch recent data from Légifrance API or data.gouv fallback"""
        docs = []
        
        # Check if Légifrance API key is available
        api_key = os.getenv("LEGIFRANCE_API_KEY")
        
        if api_key:
            # TODO: Implement actual Légifrance API when key is provided
            logger.info("Légifrance API key available but implementation pending")
            docs.extend(await self._fetch_legifrance_api(start_date, api_key))
        else:
            # Fallback to data.gouv.fr exports
            logger.info("No Légifrance API key, using data.gouv.fr fallback")
            docs.extend(await self._fetch_legifrance_datagouv(start_date))
        
        return docs
    
    async def _fetch_legifrance_api(self, start_date: datetime, api_key: str) -> List[LegalDoc]:
        """Fetch from official Légifrance API (placeholder for future implementation)"""
        # TODO: Implement when API key is provided by user
        logger.warning("Légifrance API implementation not yet available")
        return []
    
    async def _fetch_legifrance_datagouv(self, start_date: datetime) -> List[LegalDoc]:
        """Fetch from data.gouv.fr Légifrance exports"""
        docs = []
        
        try:
            # Mock data for demonstration - in real implementation, 
            # this would fetch from actual data.gouv.fr exports
            mock_docs = [
                {
                    "title": "Code civil - Article 1240 (Responsabilité délictuelle)",
                    "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032042846",
                    "date": "2024-01-15",
                    "text": "Tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui par la faute duquel il est arrivé à le réparer. La responsabilité civile délictuelle constitue un principe fondamental du droit français...",
                    "type": "code"
                },
                {
                    "title": "Décret n° 2024-123 relatif aux aides au logement",
                    "url": "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049123456",
                    "date": "2024-02-01",
                    "text": "Le Premier ministre, Sur le rapport du ministre du logement, Vu le code de la construction et de l'habitation ; Vu la loi n° 90-449 du 31 mai 1990 visant à la mise en œuvre du droit au logement...",
                    "type": "decret"
                }
            ]
            
            for item in mock_docs:
                doc_date = datetime.strptime(item["date"], "%Y-%m-%d")
                if doc_date >= start_date:
                    docs.append(LegalDoc(
                        title=item["title"],
                        url=item["url"],
                        source="legifrance",
                        date=doc_date,
                        type=item["type"],
                        text=item["text"]
                    ))
            
        except Exception as e:
            logger.error(f"Error fetching Légifrance data from data.gouv: {e}")
        
        return docs
    
    async def fetch_cour_de_cassation_recent(self, start_date: datetime) -> List[LegalDoc]:
        """Fetch recent Court of Cassation decisions"""
        docs = []
        
        try:
            # Mock data for demonstration - in real implementation,
            # this would use the actual open data API
            mock_decisions = [
                {
                    "title": "Cass. Civ. 1ère, 15 janvier 2024, n° 23-12345",
                    "url": "https://www.courdecassation.fr/decision/63d2a8f5c9e1a8f5c9e1a8f5",
                    "date": "2024-01-15",
                    "text": "La Cour de cassation, première chambre civile, a rendu un arrêt important en matière de responsabilité contractuelle. En l'espèce, il s'agissait de déterminer les conditions d'application de l'article 1231-1 du Code civil...",
                    "formation": "Première chambre civile"
                },
                {
                    "title": "Cass. Soc., 20 février 2024, n° 23-67890",
                    "url": "https://www.courdecassation.fr/decision/63d2a8f5c9e1a8f5c9e1a8f6",
                    "date": "2024-02-20",
                    "text": "En matière de droit du travail, la chambre sociale de la Cour de cassation précise les conditions du licenciement pour motif économique. L'employeur doit respecter la procédure prévue par les articles L1233-3 et suivants du Code du travail...",
                    "formation": "Chambre sociale"
                }
            ]
            
            for decision in mock_decisions:
                doc_date = datetime.strptime(decision["date"], "%Y-%m-%d")
                if doc_date >= start_date:
                    docs.append(LegalDoc(
                        title=decision["title"],
                        url=decision["url"],
                        source="cour_cassation",
                        date=doc_date,
                        type="decision",
                        jurisdiction=decision["formation"],
                        text=decision["text"]
                    ))
            
        except Exception as e:
            logger.error(f"Error fetching Cour de cassation data: {e}")
        
        return docs
    
    async def fetch_conseil_etat_recent(self, start_date: datetime) -> List[LegalDoc]:
        """Fetch recent Council of State decisions"""
        docs = []
        
        try:
            # Mock data for demonstration
            mock_decisions = [
                {
                    "title": "CE, 10 janvier 2024, n° 456789",
                    "url": "https://www.conseil-etat.fr/fr/arianeweb/CE/decision/2024-01-10/456789",
                    "date": "2024-01-10",
                    "text": "Le Conseil d'État, dans cette décision relative au droit administratif, rappelle les principes généraux applicable en matière de procédure administrative. La légalité de l'acte administratif s'apprécie au regard des règles de compétence, de forme et de fond...",
                    "formation": "Section du contentieux"
                }
            ]
            
            for decision in mock_decisions:
                doc_date = datetime.strptime(decision["date"], "%Y-%m-%d")
                if doc_date >= start_date:
                    docs.append(LegalDoc(
                        title=decision["title"],
                        url=decision["url"],
                        source="conseil_etat",
                        date=doc_date,
                        type="decision",
                        jurisdiction=decision["formation"],
                        text=decision["text"]
                    ))
            
        except Exception as e:
            logger.error(f"Error fetching Conseil d'État data: {e}")
        
        return docs
    
    async def fetch_service_public_recent(self, start_date: datetime) -> List[LegalDoc]:
        """Fetch recent service-public.fr practice sheets if authorized"""
        docs = []
        
        try:
            # Mock data for demonstration - would need authorization
            mock_fiches = [
                {
                    "title": "Aide personnalisée au logement (APL) : conditions et démarches",
                    "url": "https://www.service-public.fr/particuliers/vosdroits/F12006",
                    "date": "2024-01-25",
                    "text": "L'aide personnalisée au logement (APL) est une aide financière destinée à réduire le montant de votre loyer ou mensualité d'emprunt immobilier. Elle est versée par la Caf ou la MSA selon les conditions de ressources et la nature du logement...",
                    "category": "Logement"
                },
                {
                    "title": "Congés payés : calcul et prise des congés",
                    "url": "https://www.service-public.fr/particuliers/vosdroits/F2258",
                    "date": "2024-02-10",
                    "text": "Tout salarié a droit à des congés payés. La durée minimale est de 5 semaines soit 30 jours ouvrables par année de travail. Le calcul s'effectue selon la règle des dixièmes : 2,5 jours ouvrables par mois de travail effectif...",
                    "category": "Travail"
                }
            ]
            
            for fiche in mock_fiches:
                doc_date = datetime.strptime(fiche["date"], "%Y-%m-%d")
                if doc_date >= start_date:
                    docs.append(LegalDoc(
                        title=fiche["title"],
                        url=fiche["url"],
                        source="service_public",
                        date=doc_date,
                        type="fiche_pratique",
                        text=fiche["text"]
                    ))
            
        except Exception as e:
            logger.error(f"Error fetching Service-public.fr data: {e}")
        
        return docs


# Standalone ingestion script entry point
async def run_ingestion(since_months: int = 24):
    """Run data ingestion for the specified period"""
    start_date = datetime.now() - timedelta(days=since_months * 30)
    
    ingester = LegalDataIngester()
    results = await ingester.ingest_all_recent(start_date)
    
    print(f"Ingestion completed:")
    print(f"- Légifrance: {results['legifrance']} documents")
    print(f"- Cour de cassation: {results['cour_cassation']} documents") 
    print(f"- Conseil d'État: {results['conseil_etat']} documents")
    print(f"- Service-public.fr: {results['service_public']} documents")
    print(f"- Total chunks stored: {results['total']}")
    
    return results


if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest French legal data")
    parser.add_argument("--since", type=int, default=24, 
                       help="Ingest documents from the last N months (default: 24)")
    
    args = parser.parse_args()
    
    # Run ingestion
    asyncio.run(run_ingestion(args.since))