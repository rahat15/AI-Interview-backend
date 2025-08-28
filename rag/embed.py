from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from core.config import settings


class EmbeddingProvider:
    """Abstract base class for embedding providers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # Default dimension
    
    async def initialize(self):
        """Initialize the embedding model"""
        raise NotImplementedError
    
    async def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings"""
        raise NotImplementedError
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts in batches"""
        raise NotImplementedError


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers"""
    
    async def initialize(self):
        """Initialize the local embedding model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            print(f"Local embedding model '{self.model_name}' initialized successfully")
        except Exception as e:
            print(f"Failed to initialize local embedding model: {e}")
            # Fallback to dummy embeddings
            self.model = None
    
    async def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings"""
        if self.model is None:
            return self._generate_dummy_embeddings(texts)
        
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        
        except Exception as e:
            print(f"Local encoding failed, falling back to dummy embeddings: {e}")
            return self._generate_dummy_embeddings(texts)
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts in batches"""
        if self.model is None:
            return self._generate_dummy_embeddings(texts)
        
        try:
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
                all_embeddings.append(batch_embeddings)
            
            return np.vstack(all_embeddings)
        
        except Exception as e:
            print(f"Local batch encoding failed, falling back to dummy embeddings: {e}")
            return self._generate_dummy_embeddings(texts)
    
    def _generate_dummy_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Generate dummy embeddings for offline operation"""
        if isinstance(texts, str):
            texts = [texts]
        
        # Generate deterministic but random-looking embeddings
        embeddings = []
        for i, text in enumerate(texts):
            # Use text hash to generate consistent embeddings
            text_hash = hash(text) % (2**32)
            np.random.seed(text_hash)
            
            # Generate embedding with some structure
            embedding = np.random.normal(0, 1, self.embedding_dim)
            # Normalize to unit vector
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)
        
        return np.array(embeddings)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-ada-002"):
        super().__init__(model_name)
        self.api_key = api_key
        self.embedding_dim = 1536  # OpenAI ada-002 dimension
    
    async def initialize(self):
        """Initialize OpenAI provider"""
        # OpenAI doesn't need explicit initialization
        pass
    
    async def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) using OpenAI API"""
        try:
            import openai
            
            openai.api_key = self.api_key
            
            if isinstance(texts, str):
                texts = [texts]
            
            response = openai.Embedding.create(
                input=texts,
                model=self.model_name
            )
            
            embeddings = [data.embedding for data in response.data]
            return np.array(embeddings)
        
        except Exception as e:
            raise Exception(f"OpenAI embedding failed: {e}")
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """OpenAI handles batching automatically"""
        return await self.encode(texts)


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider"""
    
    def __init__(self, api_key: str, model_name: str = "embed-english-v3.0"):
        super().__init__(model_name)
        self.api_key = api_key
        self.embedding_dim = 1024  # Cohere v3 dimension
    
    async def initialize(self):
        """Initialize Cohere provider"""
        # Cohere doesn't need explicit initialization
        pass
    
    async def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) using Cohere API"""
        try:
            import cohere
            
            co = cohere.Client(self.api_key)
            
            if isinstance(texts, str):
                texts = [texts]
            
            response = co.embed(
                texts=texts,
                model=self.model_name,
                input_type="search_document"
            )
            
            embeddings = response.embeddings
            return np.array(embeddings)
        
        except Exception as e:
            raise Exception(f"Cohere embedding failed: {e}")
    
    async def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Cohere handles batching automatically"""
        return await self.encode(texts)


def get_embedding_provider() -> EmbeddingProvider:
    """Factory function to get the appropriate embedding provider"""
    provider_type = settings.embeddings_model.lower()
    
    if provider_type == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAIEmbeddingProvider(settings.openai_api_key)
    
    elif provider_type == "cohere":
        if not settings.cohere_api_key:
            raise ValueError("Cohere API key not configured")
        return CohereEmbeddingProvider(settings.cohere_api_key)
    
    elif provider_type == "local":
        return LocalEmbeddingProvider()
    
    else:
        print(f"Unknown embedding provider '{provider_type}', falling back to local")
        return LocalEmbeddingProvider()


# Global embedding provider instance
_embedding_provider: Optional[EmbeddingProvider] = None


async def get_embeddings(texts: Union[str, List[str]]) -> np.ndarray:
    """Get embeddings for text(s) using the configured provider"""
    global _embedding_provider
    
    if _embedding_provider is None:
        _embedding_provider = get_embedding_provider()
        await _embedding_provider.initialize()
    
    return await _embedding_provider.encode(texts)


async def get_embeddings_batch(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Get embeddings for texts in batches"""
    global _embedding_provider
    
    if _embedding_provider is None:
        _embedding_provider = get_embedding_provider()
        await _embedding_provider.initialize()
    
    return await _embedding_provider.encode_batch(texts, batch_size)


async def initialize_embeddings():
    """Initialize the embedding system"""
    global _embedding_provider
    
    if _embedding_provider is None:
        _embedding_provider = get_embedding_provider()
        await _embedding_provider.initialize()
    
    return _embedding_provider
