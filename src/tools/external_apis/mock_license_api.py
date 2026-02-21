"""
Mock State Medical Board License Verification API
Simulates real license verification with configurable failures
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, Optional

class MockLicenseAPI:
    """
    Simulates a state medical board API for license verification
    
    In production, this would call actual state APIs like:
    - California BRN (Board of Registered Nursing)
    - Texas BON (Board of Nursing)
    - AMA Physician Masterfile
    """
    
    def __init__(self, failure_rate: float = 0.0, simulate_delay: bool = True):
        """
        Initialize mock API
        
        Args:
            failure_rate: Probability of API failure (0.0 to 1.0)
            simulate_delay: Add realistic network latency
        """
        self.failure_rate = failure_rate
        self.simulate_delay = simulate_delay
        
        # Mock database of licenses
        self.mock_licenses = {
            "CA-RN-123456": {
                "license_number": "CA-RN-123456",
                "license_type": "Registered Nurse",
                "state": "California",
                "first_name": "Maria",
                "last_name": "Garcia",
                "status": "Active",
                "issue_date": "2020-03-15",
                "expiry_date": "2026-03-15",
                "discipline_actions": []
            },
            "CA-RN-789012": {
                "license_number": "CA-RN-789012",
                "license_type": "Registered Nurse",
                "state": "California",
                "first_name": "John",
                "last_name": "Smith",
                "status": "Expired",
                "issue_date": "2018-01-10",
                "expiry_date": "2024-01-10",
                "discipline_actions": []
            },
            "TX-MD-345678": {
                "license_number": "TX-MD-345678",
                "license_type": "Medical Doctor",
                "state": "Texas",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "status": "Active",
                "issue_date": "2015-06-20",
                "expiry_date": "2027-06-20",
                "discipline_actions": ["Warning - 2023-02-15"]
            },
        }
    
    def verify_license(
        self, 
        license_number: str, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict:
        """
        Verify a license against state board records
        
        Args:
            license_number: License ID (format: STATE-TYPE-NUMBER)
            first_name: Optional - for name matching
            last_name: Optional - for name matching
            
        Returns:
            dict with verification result
        """
        
        # Simulate network delay
        if self.simulate_delay:
            time.sleep(random.uniform(0.5, 2.0))
        
        # Simulate random API failures (your architectural decision in action)
        if random.random() < self.failure_rate:
            return {
                "success": False,
                "error_code": "API_TIMEOUT",
                "error_message": "State board API timeout after 30 seconds",
                "timestamp": datetime.now().isoformat(),
                "retry_after": 300  # 5 minutes
            }
        
        # Look up license
        license_data = self.mock_licenses.get(license_number)
        
        if not license_data:
            return {
                "success": True,
                "verified": False,
                "reason": "LICENSE_NOT_FOUND",
                "message": f"License {license_number} not found in state records",
                "timestamp": datetime.now().isoformat()
            }
        
        # Name matching if provided
        name_match = True
        if first_name or last_name:
            if first_name and first_name.lower() != license_data["first_name"].lower():
                name_match = False
            if last_name and last_name.lower() != license_data["last_name"].lower():
                name_match = False
        
        if not name_match:
            return {
                "success": True,
                "verified": False,
                "reason": "NAME_MISMATCH",
                "message": "Name does not match license records",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check expiry
        expiry_date = datetime.strptime(license_data["expiry_date"], "%Y-%m-%d")
        days_until_expiry = (expiry_date - datetime.now()).days
        
        # Build verification result
        # result = {
        #     "success": True,
        #     "verified": license_data["status"] == "Active",
        #     "license_data": {
        #         "license_number": license_data["license_number"],
        #         "license_type": license_data["license_type"],
        #         "state": license_data["state"],
        #         "holder_name": f"{license_data['first_name']} {license_data['last_name']}",
        #         "status": license_data["status"],
        #         "issue_date": license_data["issue_date"],
        #         "expiry_date": license_data["expiry_date"],
        #         "days_until_expiry": days_until_expiry,
        #         "discipline_actions": license_data["discipline_actions"]
        #     },
        #     "timestamp": datetime.now().isoformat()
        # }
        
        # Build verification result
        is_active = license_data["status"] == "Active"
        
        result = {
            "success": True,
            "verified": is_active,
            "license_data": {
                "license_number": license_data["license_number"],
                "license_type": license_data["license_type"],
                "state": license_data["state"],
                "holder_name": f"{license_data['first_name']} {license_data['last_name']}",
                "status": license_data["status"],
                "issue_date": license_data["issue_date"],
                "expiry_date": license_data["expiry_date"],
                "days_until_expiry": days_until_expiry,
                "discipline_actions": license_data["discipline_actions"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add reason if not verified
        if not is_active:
            result["reason"] = f"LICENSE_{license_data['status'].upper()}"
            result["message"] = f"License status is {license_data['status']}"
        # Add warnings
        warnings = []
        if days_until_expiry < 90 and days_until_expiry > 0:
            warnings.append(f"License expires in {days_until_expiry} days")
        if license_data["discipline_actions"]:
            warnings.append(f"Has {len(license_data['discipline_actions'])} disciplinary action(s)")
        
        result["warnings"] = warnings
        
        return result


# Test the API
if __name__ == "__main__":
    print("🧪 Testing Mock License Verification API\n")
    
    api = MockLicenseAPI(failure_rate=0.2, simulate_delay=False)
    
    test_cases = [
        ("CA-RN-123456", "Maria", "Garcia", "Active license"),
        ("CA-RN-789012", "John", "Smith", "Expired license"),
        ("TX-MD-345678", "Sarah", "Johnson", "Active with discipline"),
        ("NY-RN-999999", "Jane", "Doe", "License not found"),
        ("CA-RN-123456", "Wrong", "Name", "Name mismatch"),
    ]
    
    for license_num, first, last, test_name in test_cases:
        print(f"Test: {test_name}")
        print(f"  License: {license_num}")
        
        result = api.verify_license(license_num, first, last)
        
        if result["success"]:
            if result["verified"]:
                print(f"  ✅ VERIFIED")
                if "warnings" in result and result["warnings"]:
                    for warning in result["warnings"]:
                        print(f"     ⚠️  {warning}")
            else:
                print(f"  ❌ NOT VERIFIED: {result['reason']}")
        else:
            print(f"  🔴 API FAILURE: {result['error_message']}")
        
        print()