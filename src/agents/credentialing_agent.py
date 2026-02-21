"""
CareOps Credentialing Agent - Phase 2
Automates license verification for clinical staff
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
import json
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.mcp_servers.license_verification_server import MCPToolRegistry

# Load environment variables
load_dotenv()


class CredentialingAgent:
    def __init__(self):
        """Initialize Credentialing Agent with tool access"""
        
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
        
        # Initialize MCP tool registry
        self.tools = MCPToolRegistry()
        
        # System prompt - implementing your Phase 2 architectural decision
        self.system_prompt = """You are the CareOps Credentialing Agent, responsible for verifying healthcare professional licenses.

IDENTITY & ROLE
You verify licenses for nurses, physicians, and clinical staff before they begin work at CareOps Hospital Network.
You maintain the highest standards of accuracy and patient safety.

YOUR CAPABILITIES
You have access to a license verification tool that checks state medical board records.
You can verify:
- License validity and status
- Name matching against records
- Expiration dates
- Disciplinary actions

CRITICAL SAFETY RULES (Your Phase 2 Architectural Decision)
When license verification FAILS (API error, timeout, network issue):
1. IMMEDIATELY block approval - never guess or assume validity
2. ESCALATE to human credentialing officer with full context
3. LOG the failure with timestamp
4. NOTIFY the employee: "Verification pending manual review - you will be contacted within 2 hours"

When license is NOT VERIFIED (expired, not found, name mismatch):
1. BLOCK approval
2. Explain the specific reason clearly
3. Provide next steps for resolution
4. Escalate to credentialing officer

When license IS VERIFIED:
1. Report the verification details
2. Flag any warnings (expiring soon, disciplinary actions)
3. If warnings exist, recommend proactive action

RESPONSE FORMAT
Always structure your response as:
- Verification Status: [VERIFIED / NOT VERIFIED / SYSTEM ERROR]
- Details: [specific information]
- Next Steps: [what happens next]
- Reference Number: [6-digit number for tracking]

Be professional, clear, and patient-safety focused at all times.
"""
    
    def verify_credential(
        self, 
        license_number: str, 
        first_name: str = None, 
        last_name: str = None,
        verbose: bool = True
    ) -> dict:
        """
        Verify a clinical staff member's license
        
        This uses Azure OpenAI's function calling to let the agent
        decide when and how to call the license verification tool
        
        Args:
            license_number: License ID
            first_name: Optional first name
            last_name: Optional last name
            verbose: Print detailed steps
            
        Returns:
            Verification result with agent's analysis
        """
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔍 Credentialing Verification Request")
            print(f"{'='*60}")
            print(f"License: {license_number}")
            if first_name or last_name:
                print(f"Name: {first_name or ''} {last_name or ''}")
            print()
        
        # Build the user query
        query_parts = [f"Please verify license {license_number}"]
        if first_name:
            query_parts.append(f"for {first_name}")
        if last_name:
            query_parts.append(last_name)
        
        user_query = " ".join(query_parts)
        
        # Initial message
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        # Get available tools in OpenAI format
        available_functions = self.tools.get_openai_functions()
        
        try:
            # First call: Agent decides to use the tool
            if verbose:
                print("📡 Agent is analyzing the request...")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                tools=available_functions,
                tool_choice="auto",  # Let agent decide
                temperature=0.2
            )
            
            response_message = response.choices[0].message
            messages.append(response_message)
            
            # Check if agent wants to call a tool
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                if verbose:
                    print(f"🔧 Agent calling tool: {tool_calls[0].function.name}")
                
                # Execute each tool call
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if verbose:
                        print(f"   Parameters: {function_args}")
                    
                    # Execute the tool via MCP registry
                    function_response = self.tools.execute_tool(
                        function_name, 
                        **function_args
                    )
                    
                    if verbose:
                        if function_response.get("success"):
                            if function_response.get("verified"):
                                print(f"   ✅ Tool result: VERIFIED")
                            else:
                                print(f"   ❌ Tool result: NOT VERIFIED")
                        else:
                            print(f"   🔴 Tool result: API FAILURE")
                    
                    # Add tool response to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_response)
                    })
                
                # Second call: Agent interprets the tool result
                if verbose:
                    print("\n🤖 Agent is interpreting the results...")
                
                final_response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    temperature=0.2
                )
                
                agent_analysis = final_response.choices[0].message.content
                
                return {
                    "success": True,
                    "agent_response": agent_analysis,
                    "tool_result": function_response,
                    "tokens_used": response.usage.total_tokens + final_response.usage.total_tokens
                }
            
            else:
                # Agent responded without calling tools (shouldn't happen)
                return {
                    "success": True,
                    "agent_response": response_message.content,
                    "tool_result": None,
                    "tokens_used": response.usage.total_tokens
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def interactive_mode(self):
        """Run agent in interactive mode"""
        
        print("\n" + "="*60)
        print("🏥 CareOps Credentialing Agent - Interactive Mode")
        print("="*60)
        print("Available tools:", self.tools.list_tools())
        print("\nType 'quit' or 'exit' to end the session")
        print("\nExample: verify CA-RN-123456 Maria Garcia\n")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Credentialing session ended.")
                    break
                
                if not user_input:
                    continue
                
                # Parse input (simple format: "verify LICENSE_NUM [FIRST] [LAST]")
                parts = user_input.split()
                if len(parts) < 2:
                    print("Format: verify LICENSE_NUMBER [FIRST_NAME] [LAST_NAME]")
                    continue
                
                license_num = parts[1]
                first_name = parts[2] if len(parts) > 2 else None
                last_name = parts[3] if len(parts) > 3 else None
                
                result = self.verify_credential(license_num, first_name, last_name, verbose=True)
                
                if result["success"]:
                    print(f"\n{'='*60}")
                    print("📋 CREDENTIALING DECISION")
                    print(f"{'='*60}")
                    print(result["agent_response"])
                    print(f"\n[Tokens used: {result['tokens_used']}]")
                else:
                    print(f"\n❌ Error: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Test the Credentialing Agent"""
    
    print("🚀 Initializing CareOps Credentialing Agent...")
    
    try:
        agent = CredentialingAgent()
        
        print("\n" + "="*60)
        print("📋 Running Test Scenarios")
        print("="*60)
        
        test_cases = [
            ("CA-RN-123456", "Maria", "Garcia", "Valid active license"),
            ("CA-RN-789012", "John", "Smith", "Expired license"),
            ("NY-RN-999999", None, None, "License not found"),
        ]
        
        for license_num, first, last, description in test_cases:
            print(f"\n{'─'*60}")
            print(f"Test: {description}")
            print('─'*60)
            
            result = agent.verify_credential(license_num, first, last, verbose=True)
            
            if result["success"]:
                print(f"\n📋 AGENT DECISION:")
                print(result["agent_response"])
                print()
            else:
                print(f"\n❌ Error: {result['error']}\n")
        
        # Interactive mode
        print("\n" + "="*60)
        agent.interactive_mode()
        
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")


if __name__ == "__main__":
    main()