# """
# Semantic Memory Index
# Vector-based retrieval of relevant conversation chunks
# """

# import json
# import numpy as np
# from typing import List, Dict, Any, Optional
# from pathlib import Path
# from dataclasses import dataclass
# import hashlib


# @dataclass
# class IndexedChunk:
#     """Chunk with embedding"""
#     chunk_id: str
#     conversation_id: str
#     content: str
#     embedding: List[float]
#     metadata: Dict[str, Any]


# class SemanticIndex:
#     """
#     Semantic index for conversation memory
    
#     In production, this would use:
#     - Azure AI Search with vector search
#     - Cosmos DB with vector indexing
#     - Pinecone, Weaviate, or similar
    
#     For development, we use in-memory numpy arrays
#     """
    
#     def __init__(self, index_directory: str = "data/embeddings"):
#         """
#         Initialize semantic index
        
#         Args:
#             index_directory: Where to store embeddings
#         """
#         self.index_directory = Path(index_directory)
#         self.index_directory.mkdir(parents=True, exist_ok=True)
        
#         # In-memory index
#         self.chunks: List[IndexedChunk] = []
#         self.embeddings_matrix: Optional[np.ndarray] = None
    
#     def add_chunk(
#         self,
#         chunk_id: str,
#         conversation_id: str,
#         content: str,
#         embedding: List[float],
#         metadata: Optional[Dict[str, Any]] = None
#     ):
#         """
#         Add a chunk to the index
        
#         Args:
#             chunk_id: Unique chunk identifier
#             conversation_id: Parent conversation
#             content: Chunk text
#             embedding: Vector embedding
#             metadata: Additional context
#         """
        
#         chunk = IndexedChunk(
#             chunk_id=chunk_id,
#             conversation_id=conversation_id,
#             content=content,
#             embedding=embedding,
#             metadata=metadata or {}
#         )
        
#         self.chunks.append(chunk)
        
#         # Rebuild embeddings matrix
#         self._rebuild_embeddings_matrix()
    
#     def search(
#         self,
#         query_embedding: List[float],
#         top_k: int = 5,
#         conversation_id: Optional[str] = None
#     ) -> List[Dict[str, Any]]:
#         """
#         Search for relevant chunks using cosine similarity
        
#         This implements your Phase 6 decision:
#         Retrieve only the relevant parts via semantic search
        
#         Args:
#             query_embedding: Query vector
#             top_k: Number of results to return
#             conversation_id: Optional filter by conversation
            
#         Returns:
#             List of relevant chunks with similarity scores
#         """
        
#         if not self.chunks or self.embeddings_matrix is None:
#             return []
        
#         # Filter by conversation if specified
#         if conversation_id:
#             filtered_chunks = [
#                 (i, chunk) for i, chunk in enumerate(self.chunks)
#                 if chunk.conversation_id == conversation_id
#             ]
#         else:
#             filtered_chunks = list(enumerate(self.chunks))
        
#         if not filtered_chunks:
#             return []
        
#         # Get embeddings for filtered chunks
#         indices = [i for i, _ in filtered_chunks]
#         filtered_embeddings = self.embeddings_matrix[indices]
        
#         # Calculate cosine similarity
#         query_vec = np.array(query_embedding)
#         query_norm = np.linalg.norm(query_vec)
        
#         if query_norm == 0:
#             return []
        
#         # Normalize query
#         query_normalized = query_vec / query_norm
        
#         # Normalize embeddings
#         embeddings_norms = np.linalg.norm(filtered_embeddings, axis=1, keepdims=True)
#         embeddings_norms[embeddings_norms == 0] = 1  # Avoid division by zero
#         embeddings_normalized = filtered_embeddings / embeddings_norms
        
#         # Cosine similarity
#         similarities = np.dot(embeddings_normalized, query_normalized)
        
#         # Get top-k
#         top_indices = np.argsort(similarities)[-top_k:][::-1]
        
#         results = []
#         for idx in top_indices:
#             chunk_idx = indices[idx]
#             chunk = self.chunks[chunk_idx]
            
#             results.append({
#                 "chunk_id": chunk.chunk_id,
#                 "conversation_id": chunk.conversation_id,
#                 "content": chunk.content,
#                 "similarity": float(similarities[idx]),
#                 "metadata": chunk.metadata
#             })
        
#         return results
    
#     def _rebuild_embeddings_matrix(self):
#         """Rebuild embeddings matrix from chunks"""
        
#         if not self.chunks:
#             self.embeddings_matrix = None
#             return
        
#         self.embeddings_matrix = np.array([
#             chunk.embedding for chunk in self.chunks
#         ])
    
#     def save_index(self):
#         """Save index to disk"""
        
#         index_file = self.index_directory / "semantic_index.json"
        
#         index_data = {
#             "chunks": [
#                 {
#                     "chunk_id": chunk.chunk_id,
#                     "conversation_id": chunk.conversation_id,
#                     "content": chunk.content,
#                     "embedding": chunk.embedding,
#                     "metadata": chunk.metadata
#                 }
#                 for chunk in self.chunks
#             ]
#         }
        
#         with open(index_file, 'w') as f:
#             json.dump(index_data, f)
    
#     def load_index(self):
#         """Load index from disk"""
        
#         index_file = self.index_directory / "semantic_index.json"
        
#         if not index_file.exists():
#             return
        
#         with open(index_file, 'r') as f:
#             index_data = json.load(f)
        
#         self.chunks = [
#             IndexedChunk(
#                 chunk_id=chunk_data["chunk_id"],
#                 conversation_id=chunk_data["conversation_id"],
#                 content=chunk_data["content"],
#                 embedding=chunk_data["embedding"],
#                 metadata=chunk_data["metadata"]
#             )
#             for chunk_data in index_data["chunks"]
#         ]
        
#         self._rebuild_embeddings_matrix()


# def create_mock_embedding(text: str, dimensions: int = 384) -> List[float]:
#     """
#     Create a mock embedding for testing
    
#     In production, this would use:
#     - Azure OpenAI text-embedding-ada-002
#     - Azure AI Search built-in vectorizer
#     - Sentence transformers
    
#     For testing, we use a simple hash-based approach
#     that creates deterministic "embeddings"
#     """
    
#     # Use text hash to create deterministic embedding
#     text_hash = hashlib.md5(text.lower().encode()).digest()
    
#     # Create embedding from hash
#     embedding = []
#     for i in range(dimensions):
#         byte_idx = i % len(text_hash)
#         embedding.append(float(text_hash[byte_idx]) / 255.0)
    
#     # Add some text-specific features
#     word_count = len(text.split())
#     has_question = '?' in text
    
#     # Adjust embedding based on content
#     if has_question:
#         embedding[0] *= 1.5
    
#     embedding[1] *= (word_count / 100.0)
    
#     return embedding


# # Test the semantic index
# if __name__ == "__main__":
#     print("🧪 Testing Semantic Memory Index\n")
    
#     index = SemanticIndex()
    
#     print("="*60)
#     print("Indexing Conversation Chunks")
#     print("="*60)
#     print()
    
#     # Simulate chunks from Dr. Chen's conversation
#     chunks = [
#         {
#             "chunk_id": "conv-001-chunk-0000",
#             "conversation_id": "conv-001",
#             "content": """USER: When do I get my benefits?
# ASSISTANT: You're eligible after 60 days. Benefits include health insurance, 401k, and paid parental leave. Would you like me to send the enrollment forms?
# USER: What's the parental leave policy?
# ASSISTANT: Parental leave is 12 weeks paid at 100% of base salary under the Family Benefits Policy. This applies to both primary and secondary caregivers.""",
#             "metadata": {"turns": "0-3", "timestamp": "2026-02-18"}
#         },
#         {
#             "chunk_id": "conv-001-chunk-0001",
#             "conversation_id": "conv-001",
#             "content": """USER: How much PTO do I get?
# ASSISTANT: New employees receive 15 days of PTO in their first year, increasing to 20 days after 2 years of service.""",
#             "metadata": {"turns": "4-5", "timestamp": "2026-02-18"}
#         },
#         {
#             "chunk_id": "conv-001-chunk-0002",
#             "conversation_id": "conv-001",
#             "content": """USER: What about health insurance?
# ASSISTANT: Health insurance starts on your first day. We offer PPO and HMO plans through Blue Cross. You can enroll during your first 30 days.""",
#             "metadata": {"turns": "6-7", "timestamp": "2026-02-18"}
#         }
#     ]
    
#     # Index all chunks
#     for chunk in chunks:
#         embedding = create_mock_embedding(chunk["content"])
#         index.add_chunk(
#             chunk_id=chunk["chunk_id"],
#             conversation_id=chunk["conversation_id"],
#             content=chunk["content"],
#             embedding=embedding,
#             metadata=chunk["metadata"]
#         )
#         print(f"✓ Indexed: {chunk['chunk_id']}")
    
#     print(f"\nTotal chunks indexed: {len(index.chunks)}")
#     print()
    
#     # Test semantic search
#     print("="*60)
#     print("Testing Semantic Search")
#     print("="*60)
#     print()
    
#     # Query 1: About parental leave
#     print("Query 1: 'What did we discuss about parental leave?'")
#     print("-"*60)
    
#     query1 = "What did we discuss about parental leave?"
#     query1_embedding = create_mock_embedding(query1)
    
#     results1 = index.search(
#         query_embedding=query1_embedding,
#         top_k=3,
#         conversation_id="conv-001"
#     )
    
#     for i, result in enumerate(results1, 1):
#         print(f"\nResult {i} (Similarity: {result['similarity']:.4f}):")
#         print(f"  Chunk: {result['chunk_id']}")
#         print(f"  Content Preview: {result['content'][:150]}...")
    
#     print("\n")
    
#     # Query 2: About PTO
#     print("Query 2: 'How many vacation days do I get?'")
#     print("-"*60)
    
#     query2 = "How many vacation days do I get?"
#     query2_embedding = create_mock_embedding(query2)
    
#     results2 = index.search(
#         query_embedding=query2_embedding,
#         top_k=3,
#         conversation_id="conv-001"
#     )
    
#     for i, result in enumerate(results2, 1):
#         print(f"\nResult {i} (Similarity: {result['similarity']:.4f}):")
#         print(f"  Chunk: {result['chunk_id']}")
#         print(f"  Content Preview: {result['content'][:150]}...")
    
#     print("\n" + "="*60)
#     print("✅ Semantic Index Tests Complete")
#     print("="*60)
    
#     # Save index
#     index.save_index()
#     print(f"\nIndex saved to: {index.index_directory}/semantic_index.json")

# ##############################################################################

"""
Semantic Memory Index with Azure OpenAI Embeddings
Vector-based retrieval of relevant conversation chunks
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()


@dataclass
class IndexedChunk:
    """Chunk with embedding"""
    chunk_id: str
    conversation_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]


class EmbeddingService:
    """
    Azure OpenAI Embedding Service
    
    Generates vector embeddings for semantic search
    """
    
    def __init__(self):
        """Initialize Azure OpenAI client for embeddings"""
        
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_API_KEY")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.deployment_name = os.getenv("EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        print(f"✓ Embedding service initialized: {self.deployment_name}")
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding using Azure OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions for text-embedding-3-small)
        """
        
        try:
            response = self.client.embeddings.create(
                model=self.deployment_name,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            print(f"⚠️  Embedding creation failed: {e}")
            print("   Falling back to mock embedding")
            return self._create_mock_embedding(text)
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        
        try:
            response = self.client.embeddings.create(
                model=self.deployment_name,
                input=texts
            )
            
            return [item.embedding for item in response.data]
        
        except Exception as e:
            print(f"⚠️  Batch embedding failed: {e}")
            print("   Falling back to individual embeddings")
            return [self.create_embedding(text) for text in texts]
    
    def _create_mock_embedding(self, text: str, dimensions: int = 1536) -> List[float]:
        """
        Fallback: Create mock embedding for testing when Azure is unavailable
        
        This matches text-embedding-3-small dimensions (1536)
        """
        
        import hashlib
        
        # Use text hash to create deterministic embedding
        text_hash = hashlib.md5(text.lower().encode()).digest()
        
        # Create embedding from hash
        embedding = []
        for i in range(dimensions):
            byte_idx = i % len(text_hash)
            embedding.append(float(text_hash[byte_idx]) / 255.0 - 0.5)  # Center around 0
        
        # Add some text-specific features
        word_count = len(text.split())
        has_question = '?' in text
        
        # Adjust embedding based on content
        if has_question:
            embedding[0] *= 1.5
        
        embedding[1] *= (word_count / 100.0)
        
        # Normalize to unit length (like real embeddings)
        magnitude = np.linalg.norm(embedding)
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding


class SemanticIndex:
    """
    Semantic index for conversation memory
    
    Uses Azure OpenAI embeddings for production-quality semantic search
    """
    
    def __init__(self, index_directory: str = "data/embeddings"):
        """
        Initialize semantic index
        
        Args:
            index_directory: Where to store embeddings
        """
        self.index_directory = Path(index_directory)
        self.index_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding service
        self.embedding_service = EmbeddingService()
        
        # In-memory index
        self.chunks: List[IndexedChunk] = []
        self.embeddings_matrix: Optional[np.ndarray] = None
    
    def add_chunk(
        self,
        chunk_id: str,
        conversation_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a chunk to the index
        
        Args:
            chunk_id: Unique chunk identifier
            conversation_id: Parent conversation
            content: Chunk text
            embedding: Vector embedding (auto-generated if not provided)
            metadata: Additional context
        """
        
        # Generate embedding if not provided
        if embedding is None:
            embedding = self.embedding_service.create_embedding(content)
        
        chunk = IndexedChunk(
            chunk_id=chunk_id,
            conversation_id=conversation_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        self.chunks.append(chunk)
        
        # Rebuild embeddings matrix
        self._rebuild_embeddings_matrix()
    
    def add_chunks_batch(self, chunks_data: List[Dict[str, Any]]):
        """
        Add multiple chunks efficiently using batch embeddings
        
        Args:
            chunks_data: List of chunk dictionaries with chunk_id, conversation_id, content, metadata
        """
        
        # Extract texts for batch embedding
        texts = [chunk["content"] for chunk in chunks_data]
        
        # Generate embeddings in batch
        embeddings = self.embedding_service.create_embeddings_batch(texts)
        
        # Add all chunks
        for chunk_data, embedding in zip(chunks_data, embeddings):
            self.add_chunk(
                chunk_id=chunk_data["chunk_id"],
                conversation_id=chunk_data["conversation_id"],
                content=chunk_data["content"],
                embedding=embedding,
                metadata=chunk_data.get("metadata", {})
            )
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using cosine similarity
        
        This implements your Phase 6 decision:
        Retrieve only the relevant parts via semantic search
        
        Args:
            query: Query text (will be embedded automatically)
            top_k: Number of results to return
            conversation_id: Optional filter by conversation
            
        Returns:
            List of relevant chunks with similarity scores
        """
        
        if not self.chunks or self.embeddings_matrix is None:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_service.create_embedding(query)
        
        # Filter by conversation if specified
        if conversation_id:
            filtered_chunks = [
                (i, chunk) for i, chunk in enumerate(self.chunks)
                if chunk.conversation_id == conversation_id
            ]
        else:
            filtered_chunks = list(enumerate(self.chunks))
        
        if not filtered_chunks:
            return []
        
        # Get embeddings for filtered chunks
        indices = [i for i, _ in filtered_chunks]
        filtered_embeddings = self.embeddings_matrix[indices]
        
        # Calculate cosine similarity
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)
        
        if query_norm == 0:
            return []
        
        # Normalize query
        query_normalized = query_vec / query_norm
        
        # Normalize embeddings
        embeddings_norms = np.linalg.norm(filtered_embeddings, axis=1, keepdims=True)
        embeddings_norms[embeddings_norms == 0] = 1  # Avoid division by zero
        embeddings_normalized = filtered_embeddings / embeddings_norms
        
        # Cosine similarity
        similarities = np.dot(embeddings_normalized, query_normalized)
        
        # Get top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            chunk_idx = indices[idx]
            chunk = self.chunks[chunk_idx]
            
            results.append({
                "chunk_id": chunk.chunk_id,
                "conversation_id": chunk.conversation_id,
                "content": chunk.content,
                "similarity": float(similarities[idx]),
                "metadata": chunk.metadata
            })
        
        return results
    
    def _rebuild_embeddings_matrix(self):
        """Rebuild embeddings matrix from chunks"""
        
        if not self.chunks:
            self.embeddings_matrix = None
            return
        
        self.embeddings_matrix = np.array([
            chunk.embedding for chunk in self.chunks
        ])
    
    def save_index(self):
        """Save index to disk"""
        
        index_file = self.index_directory / "semantic_index.json"
        
        index_data = {
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "conversation_id": chunk.conversation_id,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                    "metadata": chunk.metadata
                }
                for chunk in self.chunks
            ]
        }
        
        with open(index_file, 'w') as f:
            json.dump(index_data, f)
    
    def load_index(self):
        """Load index from disk"""
        
        index_file = self.index_directory / "semantic_index.json"
        
        if not index_file.exists():
            return
        
        with open(index_file, 'r') as f:
            index_data = json.load(f)
        
        self.chunks = [
            IndexedChunk(
                chunk_id=chunk_data["chunk_id"],
                conversation_id=chunk_data["conversation_id"],
                content=chunk_data["content"],
                embedding=chunk_data["embedding"],
                metadata=chunk_data["metadata"]
            )
            for chunk_data in index_data["chunks"]
        ]
        
        self._rebuild_embeddings_matrix()


# Test the semantic index with real Azure OpenAI embeddings
if __name__ == "__main__":
    print("🧪 Testing Semantic Memory Index with Azure OpenAI\n")
    
    index = SemanticIndex()
    
    print("\n" + "="*60)
    print("Indexing Conversation Chunks")
    print("="*60)
    print()
    
    # Simulate chunks from Dr. Chen's conversation
    chunks = [
        {
            "chunk_id": "conv-001-chunk-0000",
            "conversation_id": "conv-001",
            "content": """USER: When do I get my benefits?
ASSISTANT: You're eligible after 60 days. Benefits include health insurance, 401k, and paid parental leave. Would you like me to send the enrollment forms?
USER: What's the parental leave policy?
ASSISTANT: Parental leave is 12 weeks paid at 100% of base salary under the Family Benefits Policy. This applies to both primary and secondary caregivers.""",
            "metadata": {"turns": "0-3", "timestamp": "2026-02-18"}
        },
        {
            "chunk_id": "conv-001-chunk-0001",
            "conversation_id": "conv-001",
            "content": """USER: How much PTO do I get?
ASSISTANT: New employees receive 15 days of PTO in their first year, increasing to 20 days after 2 years of service.""",
            "metadata": {"turns": "4-5", "timestamp": "2026-02-18"}
        },
        {
            "chunk_id": "conv-001-chunk-0002",
            "conversation_id": "conv-001",
            "content": """USER: What about health insurance?
ASSISTANT: Health insurance starts on your first day. We offer PPO and HMO plans through Blue Cross. You can enroll during your first 30 days.""",
            "metadata": {"turns": "6-7", "timestamp": "2026-02-18"}
        }
    ]
    
    # Use batch indexing for efficiency
    print("Using batch embedding for efficiency...")
    index.add_chunks_batch(chunks)
    
    print(f"✓ Indexed {len(index.chunks)} chunks")
    print()
    
    # Test semantic search with real embeddings
    print("="*60)
    print("Testing Semantic Search with Real Embeddings")
    print("="*60)
    print()
    
    # Query 1: About parental leave
    print("Query 1: 'What did we discuss about parental leave?'")
    print("-"*60)
    
    results1 = index.search(
        query="What did we discuss about parental leave?",
        top_k=3,
        conversation_id="conv-001"
    )
    
    for i, result in enumerate(results1, 1):
        print(f"\nResult {i} (Similarity: {result['similarity']:.4f}):")
        print(f"  Chunk: {result['chunk_id']}")
        print(f"  Content Preview: {result['content'][:150]}...")
    
    print("\n")
    
    # Query 2: About PTO
    print("Query 2: 'How many vacation days do I get?'")
    print("-"*60)
    
    results2 = index.search(
        query="How many vacation days do I get?",
        top_k=3,
        conversation_id="conv-001"
    )
    
    for i, result in enumerate(results2, 1):
        print(f"\nResult {i} (Similarity: {result['similarity']:.4f}):")
        print(f"  Chunk: {result['chunk_id']}")
        print(f"  Content Preview: {result['content'][:150]}...")
    
    print("\n" + "="*60)
    print("✅ Semantic Index Tests Complete")
    print("="*60)
    
    # Save index
    index.save_index()
    print(f"\nIndex saved to: {index.index_directory}/semantic_index.json")