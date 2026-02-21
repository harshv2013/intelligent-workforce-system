"""
Test API failure handling - your Phase 2 architectural decision
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.credentialing_agent import CredentialingAgent
from src.tools.mcp_servers.license_verification_server import MCPToolRegistry
from src.tools.external_apis.mock_license_api import MockLicenseAPI

# Increase failure rate to 100% to force API failure
print("🧪 Testing API Failure Handling\n")
print("Setting failure rate to 100% to simulate API downtime...\n")

# Create agent with high-failure-rate tool
agent = CredentialingAgent()

# Replace the tool's API with a high-failure version
agent.tools.tools['verify_license'].api = MockLicenseAPI(failure_rate=1.0, simulate_delay=False)

print("="*60)
print("Test: API Failure Scenario")
print("="*60)

result = agent.verify_credential(
    "CA-RN-123456",
    "Maria",
    "Garcia",
    verbose=True
)

if result["success"]:
    print(f"\n📋 AGENT DECISION DURING API FAILURE:")
    print("="*60)
    print(result["agent_response"])
    print("\n" + "="*60)
    print("\n✅ Test passed: Agent handled API failure correctly")
else:
    print(f"\n❌ Test failed: {result['error']}")