"""
MCP Server for License Verification
Exposes license verification as a tool that agents can call
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import our mock API
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.external_apis.mock_license_api import MockLicenseAPI

class LicenseVerificationTool:
    """
    MCP-compatible tool for license verification
    
    In production, this would be deployed as a standalone MCP server
    that multiple agents can connect to via HTTP/WebSocket
    """
    
    def __init__(self, failure_rate: float = 0.1):
        """
        Initialize the license verification tool
        
        Args:
            failure_rate: Simulated API failure rate (default 10%)
        """
        self.api = MockLicenseAPI(failure_rate=failure_rate, simulate_delay=True)
        self.name = "verify_license"
        self.description = """
        Verify a healthcare professional's license against state board records.
        
        This tool checks:
        - License validity and status
        - Name matching (optional)
        - Expiration dates
        - Disciplinary actions
        
        Returns verification result with warnings if license is expiring soon
        or has disciplinary actions on record.
        """
        
        # Tool schema (JSON Schema format - standard for MCP)
        self.parameters = {
            "type": "object",
            "properties": {
                "license_number": {
                    "type": "string",
                    "description": "License ID in format: STATE-TYPE-NUMBER (e.g., CA-RN-123456)",
                    "pattern": "^[A-Z]{2}-[A-Z]{2,3}-[0-9]{6}$"
                },
                "first_name": {
                    "type": "string",
                    "description": "First name of license holder (optional, for verification)"
                },
                "last_name": {
                    "type": "string",
                    "description": "Last name of license holder (optional, for verification)"
                }
            },
            "required": ["license_number"]
        }
    
    def execute(self, license_number: str, first_name: str = None, last_name: str = None) -> dict:
        """
        Execute license verification
        
        This is what the agent actually calls when using the tool
        
        Args:
            license_number: License ID
            first_name: Optional first name
            last_name: Optional last name
            
        Returns:
            Structured verification result
        """
        return self.api.verify_license(license_number, first_name, last_name)
    
    def to_openai_function(self) -> dict:
        """
        Convert tool to OpenAI function calling format
        
        This allows Azure OpenAI agents to discover and use this tool
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class MCPToolRegistry:
    """
    Registry of all available MCP tools
    
    In Phase 3, you'll expand this with more tools:
    - send_notification
    - create_calendar_event
    - update_employee_record
    - etc.
    """
    
    def __init__(self):
        self.tools = {}
        
        # Register license verification tool
        self.register_tool(LicenseVerificationTool())
    
    def register_tool(self, tool):
        """Add a tool to the registry"""
        self.tools[tool.name] = tool
        print(f"✓ Registered tool: {tool.name}")
    
    def get_tool(self, name: str):
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> list:
        """List all available tools"""
        return list(self.tools.keys())
    
    def get_openai_functions(self) -> list:
        """
        Get all tools in OpenAI function calling format
        
        This is what you pass to Azure OpenAI when creating an agent
        """
        return [tool.to_openai_function() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> dict:
        """
        Execute a tool by name with parameters
        
        This is the central dispatch point - the agent calls this
        and we route to the appropriate tool
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in registry"
            }
        
        try:
            result = tool.execute(**kwargs)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }


# Test the MCP server
if __name__ == "__main__":
    print("🔧 Testing MCP License Verification Tool\n")
    
    # Initialize tool registry
    registry = MCPToolRegistry()
    
    print(f"\nAvailable tools: {registry.list_tools()}\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Valid nurse license",
            "params": {
                "license_number": "CA-RN-123456",
                "first_name": "Maria",
                "last_name": "Garcia"
            }
        },
        {
            "name": "Expired license",
            "params": {
                "license_number": "CA-RN-789012",
                "first_name": "John",
                "last_name": "Smith"
            }
        },
        {
            "name": "License not found",
            "params": {
                "license_number": "NY-RN-999999"
            }
        }
    ]
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Params: {test['params']}")
        
        result = registry.execute_tool("verify_license", **test["params"])
        
        if result["success"]:
            if result["verified"]:
                print(f"  ✅ VERIFIED")
                license_data = result["license_data"]
                print(f"     Holder: {license_data['holder_name']}")
                print(f"     Status: {license_data['status']}")
                print(f"     Expires: {license_data['expiry_date']}")
                
                if result.get("warnings"):
                    for warning in result["warnings"]:
                        print(f"     ⚠️  {warning}")
            else:
                print(f"  ❌ NOT VERIFIED")
                print(f"     Reason: {result.get('reason', 'Unknown')}")
                if "message" in result:
                    print(f"     Message: {result['message']}")
        else:
            print(f"  🔴 API FAILURE")
            print(f"     Error: {result['error_message']}")
        
        print()
    
    # Show OpenAI function definition
    print("\n" + "="*60)
    print("OpenAI Function Definition (what agents see):")
    print("="*60)
    functions = registry.get_openai_functions()
    print(json.dumps(functions[0], indent=2))