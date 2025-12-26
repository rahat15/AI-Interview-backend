from typing import List, Dict, Any, Optional
import numpy as np
from core.models import Artifact, Embedding
from rag.embed import get_embeddings
from pymongo.collection import Collection
from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoVectorStore:
    """MongoDB vector store for embeddings"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.embeddings_collection: Collection = database.embeddings
        self.artifacts_collection: Collection = database.artifacts
    
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
        embedding_docs = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_doc = Embedding(
                artifact_id=artifact_id,
                chunk_idx=i,
                content=chunk,
                embedding=embedding.tolist()
            )
            embedding_docs.append(embedding_doc.dict(by_alias=True))
        
        # Insert all embeddings
        result = await self.embeddings_collection.insert_many(embedding_docs)
        return [str(doc_id) for doc_id in result.inserted_ids]
    
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
        
        # Build aggregation pipeline
        pipeline = []
        
        # Join with artifacts collection
        pipeline.append({
            "$lookup": {
                "from": "artifacts",
                "localField": "artifact_id",
                "foreignField": "_id",
                "as": "artifact"
            }
        })
        
        pipeline.append({"$unwind": "$artifact"})
        
        # Filter by artifact types if specified
        if artifact_types:
            pipeline.append({
                "$match": {"artifact.type": {"$in": artifact_types}}
            })
        
        # Add vector similarity calculation (cosine similarity)
        pipeline.append({
            "$addFields": {
                "similarity": {
                    "$let": {
                        "vars": {
                            "dotProduct": {
                                "$reduce": {
                                    "input": {"$range": [0, {"$size": "$embedding"}]},
                                    "initialValue": 0,
                                    "in": {
                                        "$add": [
                                            "$$value",
                                            {"$multiply": [
                                                {"$arrayElemAt": ["$embedding", "$$this"]},
                                                {"$arrayElemAt": [query_vector, "$$this"]}
                                            ]}
                                        ]
                                    }
                                }
                            },
                            "magnitude1": {
                                "$sqrt": {
                                    "$reduce": {
                                        "input": "$embedding",
                                        "initialValue": 0,
                                        "in": {"$add": ["$$value", {"$multiply": ["$$this", "$$this"]}]}
                                    }
                                }
                            },
                            "magnitude2": {
                                "$sqrt": {
                                    "$reduce": {
                                        "input": query_vector,
                                        "initialValue": 0,
                                        "in": {"$add": ["$$value", {"$multiply": ["$$this", "$$this"]}]}
                                    }
                                }
                            }
                        },
                        "in": {
                            "$divide": [
                                "$$dotProduct",
                                {"$multiply": ["$$magnitude1", "$$magnitude2"]}
                            ]
                        }
                    }
                }
            }
        })
        
        # Filter by threshold
        pipeline.append({
            "$match": {"similarity": {"$gte": threshold}}
        })
        
        # Sort by similarity and limit
        pipeline.append({"$sort": {"similarity": -1}})
        pipeline.append({"$limit": k})
        
        # Project final fields
        pipeline.append({
            "$project": {
                "id": "$_id",
                "artifact_id": 1,
                "chunk_idx": 1,
                "content": 1,
                "artifact_type": "$artifact.type",
                "artifact_meta": "$artifact.meta",
                "similarity": 1
            }
        })
        
        # Execute aggregation
        cursor = self.embeddings_collection.aggregate(pipeline)
        results = await cursor.to_list(length=k)
        
        return results
    
    async def find_similar_chunks(
        self, 
        chunk_id: str, 
        k: int = 5, 
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find chunks similar to a specific chunk"""
        # Get the target chunk
        target_chunk = await self.embeddings_collection.find_one({"_id": chunk_id})
        if not target_chunk:
            return []
        
        target_embedding = target_chunk["embedding"]
        
        # Build aggregation pipeline similar to similarity_search
        pipeline = [
            {"$match": {"_id": {"$ne": chunk_id}}},
            {
                "$lookup": {
                    "from": "artifacts",
                    "localField": "artifact_id",
                    "foreignField": "_id",
                    "as": "artifact"
                }
            },
            {"$unwind": "$artifact"},
            {
                "$addFields": {
                    "similarity": {
                        "$let": {
                            "vars": {
                                "dotProduct": {
                                    "$reduce": {
                                        "input": {"$range": [0, {"$size": "$embedding"}]},
                                        "initialValue": 0,
                                        "in": {
                                            "$add": [
                                                "$$value",
                                                {"$multiply": [
                                                    {"$arrayElemAt": ["$embedding", "$$this"]},
                                                    {"$arrayElemAt": [target_embedding, "$$this"]}
                                                ]}
                                            ]
                                        }
                                    }
                                },
                                "magnitude1": {
                                    "$sqrt": {
                                        "$reduce": {
                                            "input": "$embedding",
                                            "initialValue": 0,
                                            "in": {"$add": ["$$value", {"$multiply": ["$$this", "$$this"]}]}
                                        }
                                    }
                                },
                                "magnitude2": {
                                    "$sqrt": {
                                        "$reduce": {
                                            "input": target_embedding,
                                            "initialValue": 0,
                                            "in": {"$add": ["$$value", {"$multiply": ["$$this", "$$this"]}]}
                                        }
                                    }
                                }
                            },
                            "in": {
                                "$divide": [
                                    "$$dotProduct",
                                    {"$multiply": ["$$magnitude1", "$$magnitude2"]}
                                ]
                            }
                        }
                    }
                }
            },
            {"$match": {"similarity": {"$gte": threshold}}},
            {"$sort": {"similarity": -1}},
            {"$limit": k},
            {
                "$project": {
                    "id": "$_id",
                    "artifact_id": 1,
                    "chunk_idx": 1,
                    "content": 1,
                    "artifact_type": "$artifact.type",
                    "similarity": 1
                }
            }
        ]
        
        cursor = self.embeddings_collection.aggregate(pipeline)
        results = await cursor.to_list(length=k)
        
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
    
    async def delete_artifact_embeddings(self, artifact_id: str) -> int:
        """Delete all embeddings for an artifact"""
        result = await self.embeddings_collection.delete_many({"artifact_id": artifact_id})
        return result.deleted_count
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        total_embeddings = await self.embeddings_collection.count_documents({})
        total_artifacts = await self.artifacts_collection.count_documents({})
        
        # Get embeddings by artifact type
        pipeline = [
            {
                "$lookup": {
                    "from": "artifacts",
                    "localField": "artifact_id",
                    "foreignField": "_id",
                    "as": "artifact"
                }
            },
            {"$unwind": "$artifact"},
            {
                "$group": {
                    "_id": "$artifact.type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        cursor = self.embeddings_collection.aggregate(pipeline)
        type_counts = await cursor.to_list(length=None)
        
        stats = {
            "total_embeddings": total_embeddings,
            "total_artifacts": total_artifacts,
            "embeddings_by_type": {item["_id"]: item["count"] for item in type_counts}
        }
        
        return stats


# Factory function
async def get_vector_store(database: AsyncIOMotorDatabase) -> MongoVectorStore:
    """Get a vector store instance"""
    return MongoVectorStore(database)