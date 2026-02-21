"""
Agent-to-Agent (A2A) Communication Protocol
Standard message format for inter-agent communication
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid


class MessageType(Enum):
    """Types of A2A messages"""
    REQUEST = "request"           # Commander → Specialist
    RESPONSE = "response"         # Specialist → Commander
    NOTIFICATION = "notification" # Any agent → Any agent
    ESCALATION = "escalation"     # Specialist → Commander (needs help)
    STATUS_UPDATE = "status"      # Progress updates


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(Enum):
    """Status of an agent task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


@dataclass
class A2AMessage:
    """
    Standard A2A message format
    
    This is the "envelope" that wraps all agent-to-agent communication.
    Think of it like HTTP headers + body for agent messages.
    """
    
    # Core fields
    message_id: str
    message_type: MessageType
    from_agent: str
    to_agent: str
    timestamp: str
    
    # Content
    task_id: Optional[str] = None
    parent_task_id: Optional[str] = None  # For task hierarchies
    subject: Optional[str] = None
    payload: Dict[str, Any] = None
    
    # Metadata
    priority: MessagePriority = MessagePriority.NORMAL
    requires_response: bool = True
    correlation_id: Optional[str] = None  # Links related messages
    
    # def to_dict(self) -> Dict:
    #     """Convert to dictionary for JSON serialization"""
    #     data = asdict(self)
    #     # Convert enums to strings
    #     data['message_type'] = self.message_type.value
    #     data['priority'] = self.priority.value
    #     return data
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        
        # Convert any nested enums in payload
        if self.payload:
            data['payload'] = self._convert_enums_to_strings(self.payload)
        
        return data
    
    @staticmethod
    def _convert_enums_to_strings(obj):
        """Recursively convert enum values to strings for JSON serialization"""
        if isinstance(obj, dict):
            return {k: A2AMessage._convert_enums_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [A2AMessage._convert_enums_to_strings(item) for item in obj]
        elif isinstance(obj, Enum):
            return obj.value
        else:
            return obj
        
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'A2AMessage':
        """Create message from dictionary"""
        # Convert string enums back to enum types
        if isinstance(data.get('message_type'), str):
            data['message_type'] = MessageType(data['message_type'])
        if isinstance(data.get('priority'), str):
            data['priority'] = MessagePriority(data['priority'])
        return cls(**data)


@dataclass
class TaskRequest:
    """
    Standard task request payload
    
    This is what goes inside the A2A message when requesting work
    """
    action: str                    # What to do: "verify_license", "schedule_shift", etc.
    parameters: Dict[str, Any]     # Action-specific parameters
    context: Dict[str, Any] = None # Additional context for the agent
    deadline: Optional[str] = None # ISO 8601 datetime
    constraints: List[str] = None  # Business rules to follow


@dataclass
class TaskResponse:
    """
    Standard task response payload
    
    This is what goes inside the A2A message when returning results
    """
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = None
    recommendations: List[str] = None  # Proactive suggestions
    next_steps: List[str] = None       # What should happen next
    metadata: Dict[str, Any] = None    # Additional info


class A2AProtocol:
    """
    A2A Protocol Handler
    
    Provides helper methods for creating and parsing A2A messages
    """
    
    @staticmethod
    def create_request(
        from_agent: str,
        to_agent: str,
        task_id: str,
        action: str,
        parameters: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        context: Dict[str, Any] = None,
        parent_task_id: str = None
    ) -> A2AMessage:
        """Create a task request message"""
        
        task_request = TaskRequest(
            action=action,
            parameters=parameters,
            context=context or {}
        )
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            parent_task_id=parent_task_id,
            subject=f"Task Request: {action}",
            payload=asdict(task_request),
            priority=priority,
            requires_response=True
        )
    
    @staticmethod
    def create_response(
        from_agent: str,
        to_agent: str,
        task_id: str,
        status: TaskStatus,
        result: Dict[str, Any] = None,
        error: str = None,
        warnings: List[str] = None,
        recommendations: List[str] = None
    ) -> A2AMessage:
        """Create a task response message"""
        
        task_response = TaskResponse(
            task_id=task_id,
            status=status,
            result=result,
            error=error,
            warnings=warnings,
            recommendations=recommendations
        )
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.RESPONSE,
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            subject=f"Task Response: {status.value}",
            payload=asdict(task_response),
            requires_response=False
        )
    
    @staticmethod
    def create_escalation(
        from_agent: str,
        to_agent: str,
        task_id: str,
        reason: str,
        details: Dict[str, Any]
    ) -> A2AMessage:
        """Create an escalation message when agent needs help"""
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ESCALATION,
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            subject=f"Escalation: {reason}",
            payload={
                "reason": reason,
                "details": details,
                "blocked_status": TaskStatus.BLOCKED.value
            },
            priority=MessagePriority.HIGH,
            requires_response=True
        )


# Test the protocol
if __name__ == "__main__":
    print("🧪 Testing A2A Protocol\n")
    
    # Test 1: Create a request message
    print("=" * 60)
    print("Test 1: Task Request Message")
    print("=" * 60)
    
    request = A2AProtocol.create_request(
        from_agent="commander",
        to_agent="credentialing",
        task_id="task-001",
        action="verify_license",
        parameters={
            "license_number": "TX-MD-345678",
            "first_name": "Sarah",
            "last_name": "Chen"
        },
        priority=MessagePriority.HIGH,
        context={
            "employee_id": "EMP-2025-042",
            "position": "ER Physician",
            "onboarding_deadline": "2026-03-15"
        }
    )
    
    print(request.to_json())
    print()
    
    # Test 2: Create a response message with warning
    print("=" * 60)
    print("Test 2: Task Response with Warning (Your Decision!)")
    print("=" * 60)
    
    response = A2AProtocol.create_response(
        from_agent="credentialing",
        to_agent="commander",
        task_id="task-001",
        status=TaskStatus.COMPLETED,
        result={
            "verified": True,
            "license_status": "Active",
            "expiry_date": "2026-04-25",
            "days_until_expiry": 45
        },
        warnings=[
            "License expires in 45 days - below 90-day threshold"
        ],
        recommendations=[
            "Flag for HR Agent to track renewal",
            "Set automated reminder at 30 days before expiry",
            "Escalate if renewal proof not submitted by 2026-04-10"
        ]
    )
    
    print(response.to_json())
    print()
    
    # Test 3: Create an escalation message
    print("=" * 60)
    print("Test 3: Escalation Message (API Failure)")
    print("=" * 60)
    
    escalation = A2AProtocol.create_escalation(
        from_agent="credentialing",
        to_agent="commander",
        task_id="task-001",
        reason="External API failure",
        details={
            "api": "Texas Medical Board",
            "error": "API timeout after 30 seconds",
            "retry_attempts": 3,
            "recommendation": "Manual verification required"
        }
    )
    
    print(escalation.to_json())
    print()