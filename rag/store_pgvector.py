from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.db import get_db
from core.models import Artifact, Embedding
from rag.embed import get_embeddings


class PGVectorStore:
    """PostgreSQL vector store using pgvector extension"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def add_embeddings(
        self, 
        artifact_id: str, 
        texts: List[str], 
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """Add embeddings for an artifact's text chunks"""
        # Split text into chunks
        chunks = self._split_text_into_chunks(texts, chunk_size, overlap)
        
        # Generate embeddings for chunks
        embeddings = await get_embeddings(chunks)
        
        # Store embeddings in database
        embedding_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_embedding = Embedding(
                artifact_id=artifact_id,
                chunk_idx=i,
                content=chunk,
                embedding=embedding.tolist()  # Convert numpy array to list for pgvector
            )
            
            self.db.add(db_embedding)
            embedding_ids.append(str(db_embedding.id))
        
        self.db.commit()
        return embedding_ids
    
    def _split_text_into_chunks(
        self, 
        texts: List[str], 
        chunk_size: int, 
        overlap: int
    ) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        
        for text in texts:
            if len(text) <= chunk_size:
                chunks.append(text)
                continue
            
            # Split into overlapping chunks
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                chunks.append(chunk)
                start = end - overlap
        
        return chunks
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        artifact_types: Optional[List[str]] = None,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        # Generate query embedding
        query_embedding = await get_embeddings([query])
        query_vector = query_embedding[0].tolist()
        
        # Build query
        query_sql = """
        SELECT 
            e.id,
            e.artifact_id,
            e.chunk_idx,
            e.content,
            a.type as artifact_type,
            a.meta as artifact_meta,
            e.embedding <=> $1 as distance
        FROM embeddings e
        JOIN artifacts a ON e.artifact_id = a.id
        """
        
        params = [query_vector]
        
        if artifact_types:
            query_sql += " WHERE a.type = ANY($2)"
            params.append(artifact_types)
        
        query_sql += """
        ORDER BY e.embedding <=> $1
        LIMIT $3
        """
        params.append(k)
        
        # Execute query
        result = self.db.execute(text(query_sql), params)
        rows = result.fetchall()
        
        # Process results
        results = []
        for row in rows:
            if row.distance <= (1 - threshold):  # Convert similarity to distance
                results.append({
                    "id": row.id,
                    "artifact_id": row.artifact_id,
                    "chunk_idx": row.chunk_idx,
                    "content": row.content,
                    "artifact_type": row.artifact_type,
                    "artifact_meta": row.artifact_meta,
                    "similarity": 1 - row.distance
                })
        
        return results
    
    async def find_similar_chunks(
        self, 
        chunk_id: str, 
        k: int = 5, 
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find chunks similar to a specific chunk"""
        # Get the target chunk
        target_chunk = self.db.query(Embedding).filter(Embedding.id == chunk_id).first()
        if not target_chunk:
            return []
        
        # Search for similar chunks
        query_sql = """
        SELECT 
            e.id,
            e.artifact_id,
            e.chunk_idx,
            e.content,
            a.type as artifact_type,
            e.embedding <=> $1 as distance
        FROM embeddings e
        JOIN artifacts a ON e.artifact_id = a.id
        WHERE e.id != $2
        ORDER BY e.embedding <=> $1
        LIMIT $3
        """
        
        result = self.db.execute(
            text(query_sql), 
            [target_chunk.embedding, chunk_id, k]
        )
        rows = result.fetchall()
        
        # Process results
        results = []
        for row in rows:
            if row.distance <= (1 - threshold):
                results.append({
                    "id": row.id,
                    "artifact_id": row.artifact_id,
                    "chunk_idx": row.chunk_idx,
                    "content": row.content,
                    "artifact_type": row.artifact_type,
                    "similarity": 1 - row.distance
                })
        
        return results
    
    async def semantic_search(
        self, 
        query: str, 
        context: Dict[str, Any],
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Semantic search with context awareness"""
        # Build context-aware query
        context_text = self._build_context_text(context)
        enhanced_query = f"{query}\n\nContext: {context_text}"
        
        # Perform similarity search
        results = await self.similarity_search(enhanced_query, k)
        
        # Re-rank results based on context relevance
        ranked_results = self._rerank_by_context(results, context)
        
        return ranked_results
    
    def _build_context_text(self, context: Dict[str, Any]) -> str:
        """Build context text from context dictionary"""
        context_parts = []
        
        if "role" in context:
            context_parts.append(f"Role: {context['role']}")
        
        if "industry" in context:
            context_parts.append(f"Industry: {context['industry']}")
        
        if "company" in context:
            context_parts.append(f"Company: {context['company']}")
        
        if "competency" in context:
            context_parts.append(f"Competency: {context['competency']}")
        
        return " | ".join(context_parts)
    
    def _rerank_by_context(
        self, 
        results: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Re-rank results based on context relevance"""
        for result in results:
            # Simple context scoring
            context_score = 0
            
            if "artifact_meta" in result and result["artifact_meta"]:
                meta = result["artifact_meta"]
                
                # Check for role relevance
                if "role" in context and "role" in meta:
                    if context["role"].lower() in meta["role"].lower():
                        context_score += 0.3
                
                # Check for industry relevance
                if "industry" in context and "industry" in meta:
                    if context["industry"].lower() in meta["industry"].lower():
                        context_score += 0.2
                
                # Check for competency relevance
                if "competency" in context:
                    content_lower = result["content"].lower()
                    if context["competency"].lower() in content_lower:
                        context_score += 0.5
            
            # Combine similarity and context scores
            result["final_score"] = (0.7 * result["similarity"]) + (0.3 * context_score)
        
        # Sort by final score
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results
    
    def delete_artifact_embeddings(self, artifact_id: str) -> int:
        """Delete all embeddings for an artifact"""
        deleted_count = self.db.query(Embedding).filter(
            Embedding.artifact_id == artifact_id
        ).delete()
        
        self.db.commit()
        return deleted_count
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        total_embeddings = self.db.query(Embedding).count()
        total_artifacts = self.db.query(Artifact).count()
        
        # Get embeddings by artifact type
        type_counts = self.db.execute(text("""
            SELECT a.type, COUNT(e.id) as count
            FROM artifacts a
            LEFT JOIN embeddings e ON a.id = e.artifact_id
            GROUP BY a.type
        """)).fetchall()
        
        stats = {
            "total_embeddings": total_embeddings,
            "total_artifacts": total_artifacts,
            "embeddings_by_type": {row.type: row.count for row in type_counts}
        }
        
        return stats


# Factory function
def get_vector_store(db: Session) -> PGVectorStore:
    """Get a vector store instance"""
    return PGVectorStore(db)
