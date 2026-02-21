"""
Conversation Memory System
Stores and retrieves conversation history with semantic search
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid


@dataclass
class ConversationTurn:
    """Single turn in a conversation"""
    turn_id: str
    timestamp: str
    role: str  # "user" or "assistant"
    content: str
    agent_id: Optional[str] = None
    tokens: int = 0
    metadata: Dict[str, Any] = None


@dataclass
class Conversation:
    """Complete conversation with metadata"""
    conversation_id: str
    user_id: str
    agent_id: str
    started_at: str
    last_updated: str
    turns: List[ConversationTurn]
    total_tokens: int = 0
    status: str = "active"  # active, archived, summarized
    summary: Optional[str] = None


class ConversationMemory:
    """
    Manages conversation history with semantic retrieval
    
    Your Phase 6 architectural decision:
    - Store full conversation chunks
    - Generate embeddings per chunk
    - Retrieve only relevant parts via semantic search
    """
    
    def __init__(self, storage_directory: str = "data/conversations"):
        """
        Initialize conversation memory
        
        Args:
            storage_directory: Where to store conversations
        """
        self.storage_directory = Path(storage_directory)
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        
        # Active conversations (in-memory)
        self.active_conversations: Dict[str, Conversation] = {}
        
        # Chunk size for semantic indexing
        self.chunk_size = 5  # Chunk every 5 turns for embedding
    
    def start_conversation(
        self,
        user_id: str,
        agent_id: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Start a new conversation
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier
            conversation_id: Optional conversation ID (auto-generated if not provided)
            
        Returns:
            conversation_id
        """
        
        if not conversation_id:
            conversation_id = f"conv-{uuid.uuid4().hex[:12]}"
        
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            turns=[],
            total_tokens=0,
            status="active"
        )
        
        self.active_conversations[conversation_id] = conversation
        
        return conversation_id
    
    def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """
        Add a turn to the conversation
        
        Args:
            conversation_id: Conversation identifier
            role: "user" or "assistant"
            content: Message content
            agent_id: Which agent (for assistant turns)
            tokens: Token count
            metadata: Additional context
            
        Returns:
            ConversationTurn object
        """
        
        # Load conversation if not in memory
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = self._load_conversation(conversation_id)
        
        conversation = self.active_conversations[conversation_id]
        
        turn = ConversationTurn(
            turn_id=f"turn-{len(conversation.turns):04d}",
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            agent_id=agent_id,
            tokens=tokens,
            metadata=metadata or {}
        )
        
        conversation.turns.append(turn)
        conversation.total_tokens += tokens
        conversation.last_updated = datetime.now().isoformat()
        
        # Save after each turn
        self._save_conversation(conversation)
        
        return turn
    
    def get_recent_context(
        self,
        conversation_id: str,
        max_turns: int = 10,
        max_tokens: int = 4000
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation context for model
        
        This is the baseline approach (no semantic search yet)
        Returns most recent turns up to max_turns or max_tokens
        
        Args:
            conversation_id: Conversation identifier
            max_turns: Maximum number of turns
            max_tokens: Maximum total tokens
            
        Returns:
            List of message dicts for model
        """
        
        if conversation_id not in self.active_conversations:
            conversation = self._load_conversation(conversation_id)
        else:
            conversation = self.active_conversations[conversation_id]
        
        if not conversation:
            return []
        
        # Get most recent turns
        recent_turns = conversation.turns[-max_turns:]
        
        # Build context
        context = []
        total_tokens = 0
        
        for turn in reversed(recent_turns):
            if total_tokens + turn.tokens > max_tokens:
                break
            
            context.insert(0, {
                "role": turn.role,
                "content": turn.content
            })
            total_tokens += turn.tokens
        
        return context
    
    def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get conversation summary statistics
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Summary dictionary
        """
        
        if conversation_id not in self.active_conversations:
            conversation = self._load_conversation(conversation_id)
        else:
            conversation = self.active_conversations[conversation_id]
        
        if not conversation:
            return {}
        
        return {
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id,
            "agent_id": conversation.agent_id,
            "started_at": conversation.started_at,
            "last_updated": conversation.last_updated,
            "turn_count": len(conversation.turns),
            "total_tokens": conversation.total_tokens,
            "status": conversation.status,
            "has_summary": conversation.summary is not None
        }
    
    def chunk_conversation(
        self,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk conversation for semantic indexing
        
        This implements your Phase 6 decision:
        Break conversation into chunks that can be embedded and retrieved
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            List of chunks with metadata
        """
        
        if conversation_id not in self.active_conversations:
            conversation = self._load_conversation(conversation_id)
        else:
            conversation = self.active_conversations[conversation_id]
        
        if not conversation:
            return []
        
        chunks = []
        
        # Chunk every N turns
        for i in range(0, len(conversation.turns), self.chunk_size):
            chunk_turns = conversation.turns[i:i + self.chunk_size]
            
            # Combine turns into a chunk
            chunk_content = "\n\n".join([
                f"{turn.role.upper()}: {turn.content}"
                for turn in chunk_turns
            ])
            
            chunk_tokens = sum(turn.tokens for turn in chunk_turns)
            
            chunks.append({
                "chunk_id": f"{conversation_id}-chunk-{i//self.chunk_size:04d}",
                "conversation_id": conversation_id,
                "start_turn": i,
                "end_turn": min(i + self.chunk_size, len(conversation.turns)),
                "content": chunk_content,
                "tokens": chunk_tokens,
                "timestamp_start": chunk_turns[0].timestamp,
                "timestamp_end": chunk_turns[-1].timestamp
            })
        
        return chunks
    
    def _save_conversation(self, conversation: Conversation):
        """Save conversation to disk"""
        
        filepath = self.storage_directory / f"{conversation.conversation_id}.json"
        
        # Convert to dict
        conv_dict = asdict(conversation)
        
        with open(filepath, 'w') as f:
            json.dump(conv_dict, f, indent=2)
    
    def _load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from disk"""
        
        filepath = self.storage_directory / f"{conversation_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            conv_dict = json.load(f)
        
        # Reconstruct objects
        conv_dict['turns'] = [
            ConversationTurn(**turn) if isinstance(turn, dict) else turn
            for turn in conv_dict['turns']
        ]
        
        return Conversation(**conv_dict)


# Test the conversation memory
if __name__ == "__main__":
    print("🧪 Testing Conversation Memory System\n")
    
    memory = ConversationMemory()
    
    print("="*60)
    print("Simulating Dr. Chen's Multi-Day Conversation")
    print("="*60)
    print()
    
    # Day 1 (9 AM) - Benefits conversation with HR Agent
    print("📅 Day 1 (9 AM) - HR Agent Conversation")
    print("-"*60)
    
    conv_id = memory.start_conversation(
        user_id="EMP-PHYSICIAN-042",  # Dr. Sarah Chen
        agent_id="hr-agent"
    )
    
    print(f"Started conversation: {conv_id}\n")
    
    # Simulate conversation
    memory.add_turn(conv_id, "user", "When do I get my benefits?", tokens=50)
    memory.add_turn(
        conv_id, 
        "assistant", 
        "You're eligible after 60 days. Benefits include health insurance, 401k, and paid parental leave. Would you like me to send the enrollment forms?",
        agent_id="hr-agent",
        tokens=200
    )
    memory.add_turn(conv_id, "user", "What's the parental leave policy?", tokens=40)
    memory.add_turn(
        conv_id,
        "assistant",
        "Parental leave is 12 weeks paid at 100% of base salary under the Family Benefits Policy. This applies to both primary and secondary caregivers.",
        agent_id="hr-agent",
        tokens=180
    )
    memory.add_turn(conv_id, "user", "That's great, thank you!", tokens=30)
    
    print(f"✓ Recorded 5 turns\n")
    
    # Get summary
    summary = memory.get_conversation_summary(conv_id)
    print("Conversation Summary:")
    print(f"  Turns: {summary['turn_count']}")
    print(f"  Total Tokens: {summary['total_tokens']}")
    print(f"  Started: {summary['started_at']}")
    print()
    
    # Day 3 (10 AM) - Follow-up question
    print("="*60)
    print("📅 Day 3 (10 AM) - Follow-up Question")
    print("="*60)
    print()
    
    memory.add_turn(conv_id, "user", "What did we discuss about parental leave?", tokens=50)
    
    # Get recent context (baseline approach)
    context = memory.get_recent_context(conv_id, max_turns=10)
    
    print("Recent Context Retrieved (Last 10 turns):")
    for i, msg in enumerate(context[-3:], 1):  # Show last 3
        print(f"  {i}. {msg['role'].upper()}: {msg['content'][:80]}...")
    print()
    
    # Chunk for semantic indexing
    print("="*60)
    print("Chunking for Semantic Index")
    print("="*60)
    print()
    
    chunks = memory.chunk_conversation(conv_id)
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\n  Chunk {chunk['chunk_id']}:")
        print(f"    Turns: {chunk['start_turn']} - {chunk['end_turn']}")
        print(f"    Tokens: {chunk['tokens']}")
        print(f"    Preview: {chunk['content'][:100]}...")
    
    print("\n" + "="*60)
    print("✅ Conversation Memory Tests Complete")
    print("="*60)
    print(f"\nConversation saved to: {memory.storage_directory}/{conv_id}.json")