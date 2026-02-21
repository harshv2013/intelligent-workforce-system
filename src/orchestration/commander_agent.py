"""
CareOps Commander Agent
Orchestrator that coordinates all specialist agents
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
import json
import uuid
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestration.protocols.a2a_protocol import (
    A2AProtocol, A2AMessage, MessageType, TaskStatus, MessagePriority
)
from orchestration.protocols.agent_registry import AgentRegistry, AgentCapability

# Load environment variables
load_dotenv()


class CommanderAgent:
    """
    CareOps Commander - Multi-Agent Orchestrator
    
    Responsibilities:
    - Route requests to appropriate specialist agents
    - Coordinate multi-agent workflows
    - Track task completion across agents
    - Handle escalations from specialists
    - Implement your Phase 3 decision logic (45-day license expiry)
    """
    
    def __init__(self, registry: AgentRegistry):
        """
        Initialize Commander with agent registry
        
        Args:
            registry: AgentRegistry containing all available agents
        """
        
        # Azure configuration
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_API_KEY")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.deployment = os.getenv("GPT4O_DEPLOYMENT_NAME")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        # Agent registry
        self.registry = registry
        
        # Active tasks tracking
        self.active_tasks: Dict[str, Dict] = {}
        
        # System prompt - orchestration logic
        self.system_prompt = """You are the CareOps Commander, the orchestrator agent for CareOps Hospital Network's intelligent workforce system.

IDENTITY & ROLE
You coordinate 5 specialist agents to handle complex employee lifecycle tasks:
- HR Agent: Onboarding, benefits, policies
- Credentialing Agent: License verification
- Compliance Agent: Regulatory compliance, HIPAA, background checks
- Scheduling Agent: Shift assignments, rotations
- Insights Agent: Workforce analytics, reporting

YOUR CAPABILITIES
You do NOT perform tasks yourself. You:
1. Analyze complex requests
2. Break them into subtasks
3. Route each subtask to the appropriate specialist
4. Track completion
5. Coordinate parallel work
6. Handle escalations
7. Synthesize results into a coherent response

ORCHESTRATION PATTERNS
For simple requests (single agent needed):
- Route directly to specialist
- Wait for response
- Return result

For complex requests (multiple agents needed):
- Identify all required agents
- Determine dependencies (sequential vs parallel)
- Coordinate execution
- Aggregate results

CRITICAL DECISION LOGIC (Your Phase 3 Architectural Decision)
When Credentialing Agent reports license expiring in 45-90 days:
1. APPROVE the onboarding (license is still valid)
2. CREATE a tracking task for HR Agent
3. SET automated reminder at 30 days before expiry
4. FLAG for escalation if renewal not submitted

When any agent ESCALATES due to error:
1. Log the escalation
2. Attempt alternative approach if available
3. If no alternative: escalate to human with full context

RESPONSE FORMAT
Always structure your orchestration plan as:
- Task Breakdown: [list of subtasks]
- Assigned Agents: [which specialist handles what]
- Execution Order: [parallel or sequential]
- Expected Completion: [timeframe]

Be efficient, clear, and patient-safety focused.
"""
    
    def create_task(self, task_type: str, context: Dict[str, Any]) -> str:
        """
        Create a new orchestration task
        
        Args:
            task_type: Type of task (e.g., "physician_onboarding")
            context: Task context and parameters
            
        Returns:
            task_id
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "pending",
            "context": context,
            "subtasks": [],
            "results": {},
            "warnings": [],
            "recommendations": []
        }
        
        return task_id
    
    def route_to_agent(
        self,
        task_id: str,
        target_agent_id: str,
        action: str,
        parameters: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> A2AMessage:
        """
        Route a subtask to a specialist agent
        
        Args:
            task_id: Parent task ID
            target_agent_id: Which specialist to call
            action: What action to perform
            parameters: Action parameters
            priority: Message priority
            
        Returns:
            A2A request message
        """
        
        subtask_id = f"{task_id}-{target_agent_id}"
        
        # Create A2A request
        request = A2AProtocol.create_request(
            from_agent="commander",
            to_agent=target_agent_id,
            task_id=subtask_id,
            action=action,
            parameters=parameters,
            priority=priority,
            context=self.active_tasks[task_id]["context"],
            parent_task_id=task_id
        )
        
        # Track subtask
        self.active_tasks[task_id]["subtasks"].append({
            "subtask_id": subtask_id,
            "agent": target_agent_id,
            "action": action,
            "status": "pending",
            "request": request
        })
        
        return request
    
    def process_response(self, task_id: str, response: A2AMessage):
        """
        Process a response from a specialist agent
        
        This implements your Phase 3 decision logic for license expiry warnings
        
        Args:
            task_id: Parent task ID
            response: A2A response message
        """
        
        if task_id not in self.active_tasks:
            print(f"Warning: Unknown task {task_id}")
            return
        
        task = self.active_tasks[task_id]
        
        # Extract response payload
        payload = response.payload
        
        # Store result
        task["results"][response.from_agent] = payload
        
        # Handle warnings (YOUR PHASE 3 DECISION LOGIC)
        if payload.get("warnings"):
            for warning in payload["warnings"]:
                task["warnings"].append({
                    "from": response.from_agent,
                    "warning": warning
                })
                
                # Check for license expiry warning (45-90 days)
                if "45 days" in warning or "expir" in warning.lower():
                    # Implement your decision: Proceed but flag for tracking
                    task["recommendations"].append({
                        "type": "license_renewal_tracking",
                        "priority": "high",
                        "action": "assign_to_hr_agent",
                        "details": {
                            "employee": task["context"].get("employee_id"),
                            "license_expiry": payload.get("result", {}).get("expiry_date"),
                            "reminder_threshold": "30 days before expiry",
                            "escalation_rule": "Escalate if renewal proof not submitted",
                            "assigned_agent": "hr-agent"
                        }
                    })
        
        # Handle recommendations from specialist
        if payload.get("recommendations"):
            for rec in payload["recommendations"]:
                task["recommendations"].append({
                    "from": response.from_agent,
                    "recommendation": rec
                })
    
    def orchestrate_physician_onboarding(
        self,
        first_name: str,
        last_name: str,
        license_number: str,
        position: str,
        start_date: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrate complete physician onboarding workflow
        
        This is the big multi-agent scenario that demonstrates:
        - Parallel agent coordination
        - A2A communication
        - Your Phase 3 decision logic
        - Escalation handling
        
        Args:
            first_name: Physician's first name
            last_name: Physician's last name
            license_number: Medical license number
            position: Role (e.g., "ER Physician")
            start_date: Planned start date
            verbose: Print detailed progress
            
        Returns:
            Orchestration result with all agent outcomes
        """
        
        if verbose:
            print("\n" + "="*60)
            print("🎯 COMMANDER: Physician Onboarding Orchestration")
            print("="*60)
            print(f"Employee: Dr. {first_name} {last_name}")
            print(f"Position: {position}")
            print(f"License: {license_number}")
            print(f"Start Date: {start_date}")
            print()
        
        # Create orchestration task
        task_id = self.create_task(
            task_type="physician_onboarding",
            context={
                "employee_id": f"EMP-{uuid.uuid4().hex[:6].upper()}",
                "first_name": first_name,
                "last_name": last_name,
                "license_number": license_number,
                "position": position,
                "start_date": start_date,
                "department": "Emergency Medicine"
            }
        )
        
        if verbose:
            print(f"📋 Task ID: {task_id}\n")
        
        # Step 1: Use LLM to plan the orchestration
        if verbose:
            print("🤖 Commander analyzing orchestration plan...")
        
        planning_query = f"""
        A new physician is joining CareOps Hospital:
        - Name: Dr. {first_name} {last_name}
        - Position: {position}
        - License: {license_number}
        - Start Date: {start_date}
        
        Available specialist agents:
        {self._format_agent_capabilities()}
        
        Plan the orchestration:
        1. Which agents need to be involved?
        2. What tasks does each agent handle?
        3. Which tasks can run in parallel vs sequential?
        4. What are the dependencies?
        
        Provide a clear orchestration plan.
        """
        
        try:
            plan_response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": planning_query}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            orchestration_plan = plan_response.choices[0].message.content
            
            if verbose:
                print("\n" + "─"*60)
                print("📋 ORCHESTRATION PLAN:")
                print("─"*60)
                print(orchestration_plan)
                print()
            
            # Step 2: Execute the plan - simulate routing to each agent
            # In a real system, these would be actual A2A messages sent to running agents
            
            if verbose:
                print("="*60)
                print("🔀 ROUTING TASKS TO SPECIALIST AGENTS")
                print("="*60 + "\n")
            
            # Task 1: Credentialing (HIGH PRIORITY - blocking)
            if verbose:
                print("📤 Routing to Credentialing Agent...")
            
            cred_request = self.route_to_agent(
                task_id=task_id,
                target_agent_id="credentialing-agent",
                action="verify_license",
                parameters={
                    "license_number": license_number,
                    "first_name": first_name,
                    "last_name": last_name
                },
                priority=MessagePriority.HIGH
            )
            
            if verbose:
                print(f"   ✓ Message ID: {cred_request.message_id}")
                print(f"   ✓ Priority: {cred_request.priority.value}")
            
            # Task 2: HR (can run in parallel)
            if verbose:
                print("\n📤 Routing to HR Agent...")
            
            hr_request = self.route_to_agent(
                task_id=task_id,
                target_agent_id="hr-agent",
                action="process_onboarding",
                parameters={
                    "employee_name": f"{first_name} {last_name}",
                    "position": position,
                    "start_date": start_date
                },
                priority=MessagePriority.NORMAL
            )
            
            if verbose:
                print(f"   ✓ Message ID: {hr_request.message_id}")
            
            # Task 3: Compliance (can run in parallel)
            if verbose:
                print("\n📤 Routing to Compliance Agent...")
            
            compliance_request = self.route_to_agent(
                task_id=task_id,
                target_agent_id="compliance-agent",
                action="verify_compliance",
                parameters={
                    "employee_name": f"{first_name} {last_name}",
                    "position": position,
                    "checks_required": ["HIPAA Training", "Background Check", "Drug Screening"]
                },
                priority=MessagePriority.NORMAL
            )
            
            if verbose:
                print(f"   ✓ Message ID: {compliance_request.message_id}")
            
            # Task 4: Scheduling (depends on credentialing approval)
            if verbose:
                print("\n📤 Routing to Scheduling Agent...")
            
            schedule_request = self.route_to_agent(
                task_id=task_id,
                target_agent_id="scheduling-agent",
                action="assign_first_shift",
                parameters={
                    "employee_name": f"{first_name} {last_name}",
                    "department": "Emergency Medicine",
                    "start_date": start_date
                },
                priority=MessagePriority.NORMAL
            )
            
            if verbose:
                print(f"   ✓ Message ID: {schedule_request.message_id}")
            
            # Task 5: Insights (logging/analytics)
            if verbose:
                print("\n📤 Routing to Insights Agent...")
            
            insights_request = self.route_to_agent(
                task_id=task_id,
                target_agent_id="insights-agent",
                action="log_new_hire",
                parameters={
                    "employee_name": f"{first_name} {last_name}",
                    "position": position,
                    "department": "Emergency Medicine"
                },
                priority=MessagePriority.LOW
            )
            
            if verbose:
                print(f"   ✓ Message ID: {insights_request.message_id}")
            
            # Return orchestration summary
            return {
                "success": True,
                "task_id": task_id,
                "orchestration_plan": orchestration_plan,
                "subtasks_created": len(self.active_tasks[task_id]["subtasks"]),
                "agents_involved": [
                    "credentialing-agent",
                    "hr-agent",
                    "compliance-agent",
                    "scheduling-agent",
                    "insights-agent"
                ],
                "task": self.active_tasks[task_id]
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_agent_capabilities(self) -> str:
        """Format agent capabilities for LLM prompt"""
        lines = []
        for agent in self.registry.list_agents():
            if agent.agent_type == "specialist":
                caps = ", ".join([c.value for c in agent.capabilities])
                lines.append(f"- {agent.agent_name}: {agent.description}")
        return "\n".join(lines)


def main():
    """Test the Commander Agent"""
    
    print("🚀 Initializing CareOps Commander Agent...\n")
    
    # Create registry and register agents
    registry = AgentRegistry()
    
    # Register all 5 specialists (from earlier test)
    registry.register(
        agent_id="hr-agent",
        agent_name="HR Agent",
        agent_type="specialist",
        capabilities=[AgentCapability.POLICY_LOOKUP, AgentCapability.DOCUMENT_PROCESSING],
        description="Handles onboarding, benefits, leave policies"
    )
    
    registry.register(
        agent_id="credentialing-agent",
        agent_name="Credentialing Agent",
        agent_type="specialist",
        capabilities=[AgentCapability.LICENSE_VERIFICATION],
        description="Verifies licenses and certifications"
    )
    
    registry.register(
        agent_id="compliance-agent",
        agent_name="Compliance Agent",
        agent_type="specialist",
        capabilities=[AgentCapability.COMPLIANCE_CHECK],
        description="Ensures regulatory compliance, HIPAA, background checks"
    )
    
    registry.register(
        agent_id="scheduling-agent",
        agent_name="Scheduling Agent",
        agent_type="specialist",
        capabilities=[AgentCapability.SCHEDULE_MANAGEMENT],
        description="Manages shift scheduling and rotations"
    )
    
    registry.register(
        agent_id="insights-agent",
        agent_name="Insights Agent",
        agent_type="specialist",
        capabilities=[AgentCapability.DATA_ANALYSIS],
        description="Analyzes workforce metrics and trends"
    )
    
    print()
    
    # Create Commander
    commander = CommanderAgent(registry)
    
    # Test: Orchestrate physician onboarding
    result = commander.orchestrate_physician_onboarding(
        first_name="Sarah",
        last_name="Chen",
        license_number="TX-MD-345678",
        position="ER Physician",
        start_date="2026-03-15",
        verbose=True
    )
    
    if result["success"]:
        print("\n" + "="*60)
        print("✅ ORCHESTRATION COMPLETE")
        print("="*60)
        print(f"Task ID: {result['task_id']}")
        print(f"Agents Coordinated: {len(result['agents_involved'])}")
        print(f"Subtasks Created: {result['subtasks_created']}")
        print()
    else:
        print(f"\n❌ Orchestration failed: {result['error']}")


if __name__ == "__main__":
    main()