"""
CareOps HR Agent - Phase 1
Handles employee HR queries with intelligent model routing
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
import json

# Load environment variables
load_dotenv()

class HRAgent:
    def __init__(self):
        """Initialize the HR Agent with Azure OpenAI clients"""

        # Azure configuration
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_API_KEY")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.gpt4o_deployment = os.getenv("GPT4O_DEPLOYMENT_NAME")
        self.phi_deployment = os.getenv("PHI_DEPLOYMENT_NAME")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        # # Initialize Azure OpenAI client
        # # Extract base URL from project endpoint
        # base_url = self.endpoint.replace("/api/projects/proj-default", "")
        
        # self.client = AzureOpenAI(
        #     azure_endpoint=base_url,
        #     api_key=self.api_key,
        #     api_version="2024-08-01-preview"
        # )
        
        # Load knowledge base
        self.knowledge_base = self._load_policies()
        
        # System prompt from your Phase 0 decisions
        self.system_prompt = """You are the CareOps HR Agent, a professional and empathetic HR assistant for CareOps Hospital Network employees.

                                IDENTITY & ROLE
                                You assist CareOps employees with HR policy questions, onboarding guidance, benefits information, leave queries, and scheduling policy questions.
                                You represent the CareOps HR department and maintain a professional, supportive, and clear tone at all times.

                                KNOWLEDGE BOUNDARIES
                                You ALWAYS answer based strictly on the CareOps HR policy documents provided. You ALWAYS cite the specific policy document and section when answering.
                                Example citation format: "According to the CareOps Leave & PTO Policy (Section: PTO Accrual)..."

                                You NEVER provide:
                                - Medical advice of any kind
                                - Legal interpretations beyond what is written in policy
                                - Payroll calculations outside defined policy rules
                                - Access to any employee's personal data
                                - Information the user is not authorized to access based on their role

                                ESCALATION RULES
                                You MUST escalate to a human HR representative when:
                                - The query involves a policy exception request
                                - The query involves a dispute or formal grievance
                                - The query involves disciplinary action
                                - The query contains legal threats or mentions of lawyers
                                - The employee expresses emotional distress
                                - Your confidence in the policy grounding is below 75%
                                - Required documentation is missing or unclear

                                When escalating, say exactly:
                                "This requires personal attention from our HR team. I'm connecting you with an HR representative now. Reference number: [generate a 6-digit reference number]. They will contact you within 1 business day."

                                CONFIDENCE & GROUNDING
                                If you cannot find a clear answer in the provided documents:
                                - Do NOT guess or infer beyond policy text
                                - Say: "I don't have enough information in our current policy documents to answer this accurately. Let me connect you with an HR representative."

                                SCOPE BOUNDARIES
                                You do NOT handle:
                                - Clinical or medical decisions → refer to Clinical team
                                - Payroll disputes → refer to Finance Agent
                                - Compliance or HIPAA issues → refer to Compliance Agent
                                - IT setup beyond what's in the onboarding guide → refer to IT

                                RESPONSE FORMAT
                                - Keep answers concise and clear
                                - Use bullet points for multi-step processes
                                - Always end with: "Is there anything else I can help you with today?"
                                """
    
    def _load_policies(self):
        """Load all HR policy documents from data/policies/"""
        policies_dir = Path("data/policies")
        knowledge = {}
        
        if not policies_dir.exists():
            print(f"Warning: Policies directory not found at {policies_dir}")
            return knowledge
        
        for policy_file in policies_dir.glob("*.md"):
            try:
                with open(policy_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    knowledge[policy_file.stem] = content
                    print(f"✓ Loaded: {policy_file.name}")
            except Exception as e:
                print(f"✗ Error loading {policy_file.name}: {e}")
        
        return knowledge
    
    # def _classify_complexity(self, query: str) -> str:
    #     """
    #     Determine if query should go to GPT-4o or Phi
    #     Based on your Decision 1 routing logic
    #     """
        
    #     # Keywords that indicate complex reasoning needed
    #     complex_keywords = [
    #         "exception", "appeal", "legal", "dispute", "conflict",
    #         "combine", "multiple", "interact", "edge case", "what if",
    #         "policy conflict", "interpretation", "draft", "write"
    #     ]
        
    #     # Check for complex indicators
    #     query_lower = query.lower()
        
    #     # Multi-intent detection (mentions multiple policy areas)
    #     policy_mentions = sum([
    #         "pto" in query_lower or "leave" in query_lower,
    #         "benefit" in query_lower or "insurance" in query_lower,
    #         "schedule" in query_lower or "shift" in query_lower,
    #         "onboard" in query_lower or "credential" in query_lower,
    #         "maternity" in query_lower or "paternity" in query_lower
    #     ])
        
    #     # Route to GPT-4o if complex
    #     if policy_mentions >= 2:
    #         return "gpt-4o"
        
    #     if any(keyword in query_lower for keyword in complex_keywords):
    #         return "gpt-4o"
        
    #     if len(query.split()) > 20:  # Long queries likely complex
    #         return "gpt-4o"
        
    #     # Simple queries go to Phi
    #     return "phi"

    def _classify_complexity(self, query: str) -> str:
        """
        Determine if query should go to GPT-4o or Phi
        
        Phase 1: Always route to GPT-4o for reliable grounding
        Phase 2: Will implement proper model routing with Azure AI Search
        """
        
        # TODO Phase 2: Re-enable Phi routing once Azure AI Search is added
        # Phi-4-mini needs better retrieval infrastructure for reliable grounding
        # Current finding: Phi ignores document context and uses pre-trained knowledge
        
        return "gpt-4o"  # Always use GPT-4o in Phase 1
    
    def _prepare_context(self, query: str) -> str:
        """Prepare knowledge base context for the query"""
        
        # In Phase 1, we'll do simple keyword matching
        # In Phase 2, you'll add semantic search via Azure AI Search
        
        context = "CareOps HR Policy Knowledge Base:\n\n"
        
        for policy_name, content in self.knowledge_base.items():
            context += f"--- {policy_name.replace('-', ' ').title()} ---\n"
            context += content + "\n\n"
        
        return context
    
    def query(self, user_query: str, verbose: bool = True) -> dict:
        """
        Process an HR query with intelligent model routing
        
        Args:
            user_query: The employee's question
            verbose: Print routing decisions
            
        Returns:
            dict with response, model_used, and metadata
        """
        
        # Classify complexity
        model_choice = self._classify_complexity(user_query)
        print(f"model_choice : {model_choice}")
        deployment = (self.gpt4o_deployment if model_choice == "gpt-4o" 
                     else self.phi_deployment)
        
        # deployment  = self.phi_deployment
        # deployment  = self.gpt4o_deployment
        
        if verbose:
            print(f"\n🔀 Routing to: {model_choice.upper()}")
            print(f"   Deployment: {deployment}")
        
        # Prepare context
        context = self._prepare_context(user_query)
        
        # # Build messages
        # messages = [
        #     {"role": "system", "content": self.system_prompt},
        #     {"role": "system", "content": context},
        #     {"role": "user", "content": user_query}
        # ]

        # Build messages with model-specific reinforcement
        if model_choice == "phi":
            # Phi needs VERY explicit grounding instructions
            phi_reinforcement = """
                                CRITICAL: You MUST answer ONLY using the CareOps policy documents provided below.
                                Do NOT use your general knowledge about HR policies.
                                Do NOT give generic answers.
                                ONLY cite information from the CareOps documents.
                                If the answer is not in the documents, say so and escalate.
                                """
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": phi_reinforcement},
                {"role": "system", "content": context},
                {"role": "user", "content": user_query}
            ]
        else:
            # GPT-4o handles grounding well
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": context},
                {"role": "user", "content": user_query}
            ]
        
        try:
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=0.3,  # Low temperature for factual responses
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "response": answer,
                "model_used": model_choice,
                "deployment": deployment,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": model_choice
            }
    
    def interactive_mode(self):
        """Run the agent in interactive chat mode"""
        
        print("\n" + "="*60)
        print("🏥 CareOps HR Agent - Interactive Mode")
        print("="*60)
        print(f"Knowledge base loaded: {len(self.knowledge_base)} policy documents")
        print("Type 'quit' or 'exit' to end the session\n")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thank you for using CareOps HR Agent!")
                    break
                
                if not user_input:
                    continue
                
                # Process query
                result = self.query(user_input, verbose=True)
                
                if result["success"]:
                    print(f"\n🤖 HR Agent: {result['response']}")
                    print(f"\n   [Model: {result['model_used']} | Tokens: {result['tokens_used']}]")
                else:
                    print(f"\n❌ Error: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")


def main():
    """Main entry point for testing"""
    
    print("🚀 Initializing CareOps HR Agent...")
    
    try:
        agent = HRAgent()
        
        # Test with your 3 scenarios from Phase 0
        print("\n" + "="*60)
        print("📋 Running Test Scenarios")
        print("="*60)
        
        test_queries = [
            "How many PTO days do I get in my first year?",
            "I'm a nurse on a 6-month travel contract. I just had a baby. Am I eligible for maternity leave and how does it interact with my FMLA eligibility?",
            "My manager gave me a written warning that I think is unfair and I'm considering legal action."
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'─'*60}")
            print(f"Test {i}: {query}")
            print('─'*60)
            
            result = agent.query(query, verbose=True)
            
            if result["success"]:
                print(f"\n✅ Response:\n{result['response']}\n")
            else:
                print(f"\n❌ Error: {result['error']}\n")
        
        # Start interactive mode
        print("\n" + "="*60)
        agent.interactive_mode()
        
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file exists and has correct values")
        print("2. Verify policy documents are in data/policies/")
        print("3. Ensure Azure deployments are named correctly")


if __name__ == "__main__":
    main()