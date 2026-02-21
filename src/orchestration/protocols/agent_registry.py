"""
Agent Registry
Central registry for agent discovery and routing
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class AgentCapability(Enum):
    """Standard agent capabilities"""
    LICENSE_VERIFICATION = "license_verification"
    POLICY_LOOKUP = "policy_lookup"
    SCHEDULE_MANAGEMENT = "schedule_management"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    NOTIFICATION = "notification"


@dataclass
class AgentMetadata:
    """Metadata about a registered agent"""
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: List[AgentCapability]
    description: str
    version: str = "1.0.0"
    status: str = "active"
    
    # Handler function (the actual agent instance)
    handler: Optional[Callable] = None


class AgentRegistry:
    """
    Central registry for all agents in the system
    
    This is how the Commander knows which agents exist
    and what they can do
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentMetadata] = {}
        print("✓ Agent Registry initialized")
    
    def register(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        description: str,
        handler: Optional[Callable] = None
    ) -> AgentMetadata:
        """
        Register an agent with the system
        
        Args:
            agent_id: Unique identifier (e.g., "hr-agent")
            agent_name: Display name (e.g., "HR Agent")
            agent_type: Type (e.g., "specialist")
            capabilities: What the agent can do
            description: What the agent handles
            handler: Function to call the agent
            
        Returns:
            AgentMetadata object
        """
        
        metadata = AgentMetadata(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type=agent_type,
            capabilities=capabilities,
            description=description,
            handler=handler
        )
        
        self.agents[agent_id] = metadata
        print(f"✓ Registered: {agent_name} ({agent_id})")
        
        return metadata
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        return self.agents.get(agent_id)
    
    def find_by_capability(self, capability: AgentCapability) -> List[AgentMetadata]:
        """Find all agents with a specific capability"""
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities
        ]
    
    def list_agents(self) -> List[AgentMetadata]:
        """List all registered agents"""
        return list(self.agents.values())
    
    def get_agent_ids(self) -> List[str]:
        """Get list of all agent IDs"""
        return list(self.agents.keys())


# Test the registry
if __name__ == "__main__":
    print("🧪 Testing Agent Registry\n")
    
    registry = AgentRegistry()
    
    print("\n" + "="*60)
    print("Registering Agents")
    print("="*60 + "\n")
    
    # Register all 6 agents
    registry.register(
        agent_id="hr-agent",
        agent_name="HR Agent",
        agent_type="specialist",
        capabilities=[
            AgentCapability.POLICY_LOOKUP,
            AgentCapability.DOCUMENT_PROCESSING
        ],
        description="Handles onboarding, benefits, leave policies"
    )
    
    registry.register(
        agent_id="credentialing-agent",
        agent_name="Credentialing Agent",
        agent_type="specialist",
        capabilities=[
            AgentCapability.LICENSE_VERIFICATION,
            AgentCapability.COMPLIANCE_CHECK
        ],
        description="Verifies licenses and certifications"
    )
    
    registry.register(
        agent_id="compliance-agent",
        agent_name="Compliance Agent",
        agent_type="specialist",
        capabilities=[
            AgentCapability.COMPLIANCE_CHECK,
            AgentCapability.POLICY_LOOKUP
        ],
        description="Ensures regulatory compliance"
    )
    
    registry.register(
        agent_id="scheduling-agent",
        agent_name="Scheduling Agent",
        agent_type="specialist",
        capabilities=[
            AgentCapability.SCHEDULE_MANAGEMENT
        ],
        description="Manages shift scheduling and rotations"
    )
    
    registry.register(
        agent_id="insights-agent",
        agent_name="Insights Agent",
        agent_type="specialist",
        capabilities=[
            AgentCapability.DATA_ANALYSIS
        ],
        description="Analyzes workforce metrics and trends"
    )
    
    registry.register(
        agent_id="commander",
        agent_name="CareOps Commander",
        agent_type="orchestrator",
        capabilities=[],  # Orchestrators don't have task capabilities
        description="Routes and coordinates all agents"
    )
    
    # Test capability-based discovery
    print("\n" + "="*60)
    print("Testing Capability-Based Discovery")
    print("="*60 + "\n")
    
    license_agents = registry.find_by_capability(AgentCapability.LICENSE_VERIFICATION)
    print(f"Agents with LICENSE_VERIFICATION capability:")
    for agent in license_agents:
        print(f"  - {agent.agent_name} ({agent.agent_id})")
    
    compliance_agents = registry.find_by_capability(AgentCapability.COMPLIANCE_CHECK)
    print(f"\nAgents with COMPLIANCE_CHECK capability:")
    for agent in compliance_agents:
        print(f"  - {agent.agent_name} ({agent.agent_id})")
    
    # List all agents
    print("\n" + "="*60)
    print("All Registered Agents")
    print("="*60 + "\n")
    
    for agent in registry.list_agents():
        caps = ", ".join([c.value for c in agent.capabilities])
        print(f"{agent.agent_name}")
        print(f"  ID: {agent.agent_id}")
        print(f"  Type: {agent.agent_type}")
        print(f"  Capabilities: {caps or 'Orchestrator'}")
        print(f"  Description: {agent.description}")
        print()