"""
Vector store abstraction for legal document search
Supports pgvector (via Supabase) with local SQLite+faiss fallback
"""
import os
import logging
import json
import sqlite3
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from openai import OpenAI

from .models import LegalDoc, VectorSearchResult

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract vector store interface"""
    
    @abstractmethod
    async def upsert(self, docs: List[LegalDoc]) -> bool:
        """Insert or update documents in the vector store"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        k: int = 10, 
        since_date: Optional[datetime] = None
    ) -> List[VectorSearchResult]:
        """Search documents by query with optional date filter"""
        pass


class LocalVectorStore(VectorStore):
    """Local SQLite + FAISS fallback implementation"""
    
    def __init__(self):
        self.db_path = "legal_docs.db"
        self.openai_client = None
        
        # Initialize OpenAI client if available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        
        self._init_db()
        
        # Try to import faiss for vector similarity
        try:
            import faiss
            self.faiss = faiss
            self.index = None
            self._load_index()
        except ImportError:
            logger.warning("FAISS not available, falling back to text similarity")
            self.faiss = None
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS legal_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                jurisdiction TEXT,
                text TEXT NOT NULL,
                embedding TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def _load_index(self):
        """Load FAISS index if exists"""
        if not self.faiss:
            return
        
        try:
            if os.path.exists("legal_docs.index"):
                self.index = self.faiss.read_index("legal_docs.index")
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                # Create empty index (will be populated on first upsert)
                self.index = self.faiss.IndexFlatIP(1536)  # OpenAI embedding size
                logger.info("Created new FAISS index")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            self.index = None
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get OpenAI embedding for text"""
        if not self.openai_client:
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]  # Limit input size
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    async def upsert(self, docs: List[LegalDoc]) -> bool:
        """Insert or update documents"""
        try:
            conn = sqlite3.connect(self.db_path)
            embeddings = []
            
            for doc in docs:
                # Get embedding
                embedding = self._get_embedding(doc.text)
                embedding_json = json.dumps(embedding) if embedding else None
                
                # Store in SQLite
                conn.execute("""
                    INSERT OR REPLACE INTO legal_documents 
                    (title, url, source, date, type, jurisdiction, text, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.title,
                    doc.url,
                    doc.source,
                    doc.date.isoformat(),
                    doc.type,
                    doc.jurisdiction,
                    doc.text,
                    embedding_json
                ))
                
                if embedding:
                    embeddings.append(embedding)
            
            conn.commit()
            conn.close()
            
            # Update FAISS index if available
            if self.faiss and self.index is not None and embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                self.index.add(embeddings_array)
                self.faiss.write_index(self.index, "legal_docs.index")
                logger.info(f"Added {len(embeddings)} vectors to FAISS index")
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting documents: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        k: int = 10, 
        since_date: Optional[datetime] = None
    ) -> List[VectorSearchResult]:
        """Search documents"""
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            
            conn = sqlite3.connect(self.db_path)
            
            # Build SQL query with date filter
            sql = """
                SELECT title, url, source, date, type, jurisdiction, text, embedding
                FROM legal_documents
            """
            params = []
            
            if since_date:
                sql += " WHERE date >= ?"
                params.append(since_date.isoformat())
            
            sql += " ORDER BY date DESC LIMIT ?"
            params.append(k * 2)  # Get more docs for reranking
            
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                title, url, source, date_str, type_, jurisdiction, text, embedding_json = row
                
                # Create LegalDoc
                doc = LegalDoc(
                    title=title,
                    url=url,
                    source=source,
                    date=datetime.fromisoformat(date_str),
                    type=type_,
                    jurisdiction=jurisdiction,
                    text=text
                )
                
                # Calculate relevance score
                score = 0.5  # Default text similarity
                if query_embedding and embedding_json:
                    try:
                        doc_embedding = json.loads(embedding_json)
                        # Simple cosine similarity
                        dot_product = np.dot(query_embedding, doc_embedding)
                        norm_query = np.linalg.norm(query_embedding)
                        norm_doc = np.linalg.norm(doc_embedding)
                        score = dot_product / (norm_query * norm_doc)
                    except:
                        pass
                
                # Add freshness boost (more recent = higher score)
                days_old = (datetime.now() - doc.date).days
                freshness_factor = max(0.1, 1.0 - (days_old / 730))  # 2 years decay
                relevance = score * 0.8 + freshness_factor * 0.2
                
                results.append(VectorSearchResult(
                    doc=doc,
                    score=score,
                    relevance=relevance
                ))
            
            # Sort by relevance and return top k
            results.sort(key=lambda x: x.relevance, reverse=True)
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []


class SupabaseVectorStore(VectorStore):
    """Supabase pgvector implementation"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.openai_client = None
        
        if not (self.url and self.key):
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY required")
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        
        # Try to import supabase
        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
        except ImportError:
            raise ImportError("supabase-py package required for SupabaseVectorStore")
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get OpenAI embedding for text"""
        if not self.openai_client:
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    async def upsert(self, docs: List[LegalDoc]) -> bool:
        """Insert or update documents in Supabase"""
        try:
            data = []
            for doc in docs:
                embedding = self._get_embedding(doc.text)
                
                data.append({
                    'title': doc.title,
                    'url': doc.url,
                    'source': doc.source,
                    'date': doc.date.isoformat(),
                    'type': doc.type,
                    'jurisdiction': doc.jurisdiction,
                    'text': doc.text,
                    'embedding': embedding
                })
            
            result = self.client.table('legal_documents').upsert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error upserting to Supabase: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        k: int = 10, 
        since_date: Optional[datetime] = None
    ) -> List[VectorSearchResult]:
        """Search documents in Supabase using pgvector"""
        try:
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []
            
            # Build query
            query_builder = self.client.table('legal_documents').select('*')
            
            if since_date:
                query_builder = query_builder.gte('date', since_date.isoformat())
            
            # TODO: Add pgvector similarity search when fully implemented
            # For now, fallback to simple text search
            result = query_builder.limit(k).execute()
            
            search_results = []
            for row in result.data:
                doc = LegalDoc(
                    title=row['title'],
                    url=row['url'],
                    source=row['source'],
                    date=datetime.fromisoformat(row['date']),
                    type=row['type'],
                    jurisdiction=row.get('jurisdiction'),
                    text=row['text']
                )
                
                # Simple relevance calculation
                score = 0.5
                if row.get('embedding') and query_embedding:
                    try:
                        doc_embedding = row['embedding']
                        dot_product = np.dot(query_embedding, doc_embedding)
                        norm_query = np.linalg.norm(query_embedding)
                        norm_doc = np.linalg.norm(doc_embedding)
                        score = dot_product / (norm_query * norm_doc)
                    except:
                        pass
                
                days_old = (datetime.now() - doc.date).days
                freshness_factor = max(0.1, 1.0 - (days_old / 730))
                relevance = score * 0.8 + freshness_factor * 0.2
                
                search_results.append(VectorSearchResult(
                    doc=doc,
                    score=score,
                    relevance=relevance
                ))
            
            search_results.sort(key=lambda x: x.relevance, reverse=True)
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching Supabase: {e}")
            return []


def get_vector_store() -> VectorStore:
    """Factory function to get appropriate vector store"""
    # Try Supabase first
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        try:
            return SupabaseVectorStore()
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase vector store: {e}")
    
    # Fallback to local
    logger.info("Using local vector store")
    return LocalVectorStore()