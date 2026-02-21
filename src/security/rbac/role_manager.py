"""
Role-Based Access Control (RBAC) for CareOps Agents
Implements your Phase 4 decision: Role-scoped data access
"""

from enum import Enum
from typing import List, Dict, Optional, Set
from dataclasses import dataclass


class UserRole(Enum):
    """User roles in CareOps system"""
    NURSE = "nurse"
    PHYSICIAN = "physician"
    HR_ADMIN = "hr_admin"
    HR_STAFF = "hr_staff"
    FINANCE = "finance"
    COMPLIANCE_OFFICER = "compliance_officer"
    MANAGER = "manager"
    SYSTEM_ADMIN = "system_admin"


class DataCategory(Enum):
    """Categories of data with different access requirements"""
    # HR data
    OWN_COMPENSATION = "own_compensation"
    ALL_COMPENSATION = "all_compensation"
    OWN_BENEFITS = "own_benefits"
    ALL_BENEFITS = "all_benefits"
    OWN_PERFORMANCE = "own_performance"
    ALL_PERFORMANCE = "all_performance"
    
    # Credentialing data
    OWN_CREDENTIALS = "own_credentials"
    ALL_CREDENTIALS = "all_credentials"
    LICENSE_VERIFICATION = "license_verification"
    
    # Scheduling data
    OWN_SCHEDULE = "own_schedule"
    DEPARTMENT_SCHEDULE = "department_schedule"
    ALL_SCHEDULES = "all_schedules"
    
    # Analytics data
    WORKFORCE_METRICS = "workforce_metrics"
    FINANCIAL_ANALYTICS = "financial_analytics"
    
    # System data
    AUDIT_LOGS = "audit_logs"
    SYSTEM_CONFIG = "system_config"


@dataclass
class AccessAttempt:
    """Record of an access attempt for auditing"""
    user_id: str
    user_role: UserRole
    requested_data: DataCategory
    target_employee_id: Optional[str]
    granted: bool
    reason: str
    timestamp: str


class RoleManager:
    """
    RBAC Manager implementing your Phase 4 decision logic
    
    Key principle: Users access only the minimum data necessary for their role
    """
    
    def __init__(self):
        # Define role permissions
        self.role_permissions = self._initialize_permissions()
    
    def _initialize_permissions(self) -> Dict[UserRole, Set[DataCategory]]:
        """
        Initialize role-based permissions
        
        This implements your RBAC matrix from Phase 4
        """
        return {
            UserRole.NURSE: {
                DataCategory.OWN_COMPENSATION,
                DataCategory.OWN_BENEFITS,
                DataCategory.OWN_SCHEDULE,
                DataCategory.OWN_CREDENTIALS,
                DataCategory.OWN_PERFORMANCE
            },
            
            UserRole.PHYSICIAN: {
                DataCategory.OWN_COMPENSATION,
                DataCategory.OWN_BENEFITS,
                DataCategory.OWN_SCHEDULE,
                DataCategory.OWN_CREDENTIALS,
                DataCategory.OWN_PERFORMANCE,
                DataCategory.DEPARTMENT_SCHEDULE  # Physicians see their department
            },
            
            UserRole.HR_ADMIN: {
                DataCategory.ALL_COMPENSATION,
                DataCategory.ALL_BENEFITS,
                DataCategory.ALL_PERFORMANCE,
                DataCategory.ALL_CREDENTIALS,
                DataCategory.ALL_SCHEDULES,
                DataCategory.WORKFORCE_METRICS,
                DataCategory.AUDIT_LOGS
            },
            
            UserRole.HR_STAFF: {
                DataCategory.OWN_COMPENSATION,
                DataCategory.OWN_BENEFITS,
                DataCategory.ALL_CREDENTIALS,  # HR staff verify credentials
                DataCategory.WORKFORCE_METRICS
            },
            
            UserRole.FINANCE: {
                DataCategory.ALL_COMPENSATION,
                DataCategory.FINANCIAL_ANALYTICS,
                DataCategory.WORKFORCE_METRICS
            },
            
            UserRole.COMPLIANCE_OFFICER: {
                DataCategory.ALL_CREDENTIALS,
                DataCategory.LICENSE_VERIFICATION,
                DataCategory.AUDIT_LOGS,
                DataCategory.WORKFORCE_METRICS
            },
            
            UserRole.MANAGER: {
                DataCategory.OWN_COMPENSATION,
                DataCategory.OWN_BENEFITS,
                DataCategory.DEPARTMENT_SCHEDULE,
                DataCategory.ALL_PERFORMANCE,  # Managers see team performance
                DataCategory.WORKFORCE_METRICS
            },
            
            UserRole.SYSTEM_ADMIN: set(DataCategory)  # Full access
        }
    
    def check_access(
        self,
        user_id: str,
        user_role: UserRole,
        requested_data: DataCategory,
        target_employee_id: Optional[str] = None
    ) -> AccessAttempt:
        """
        Check if a user can access specific data
        
        This implements your Phase 4 decision:
        "Answer only the nurse's own salary range, not Dr. Chen's"
        
        Args:
            user_id: ID of the requesting user
            user_role: Role of the requesting user
            requested_data: Category of data being requested
            target_employee_id: ID of the employee whose data is requested
                              (None = own data, or aggregate data)
        
        Returns:
            AccessAttempt with granted True/False and reason
        """
        
        from datetime import datetime
        
        # Get user's permissions
        user_permissions = self.role_permissions.get(user_role, set())
        
        # Check 1: Does the role have permission for this data category?
        if requested_data not in user_permissions:
            return AccessAttempt(
                user_id=user_id,
                user_role=user_role,
                requested_data=requested_data,
                target_employee_id=target_employee_id,
                granted=False,
                reason=f"Role '{user_role.value}' does not have access to '{requested_data.value}'",
                timestamp=datetime.now().isoformat()
            )
        
        # Check 2: If requesting someone else's data, is it allowed?
        if target_employee_id and target_employee_id != user_id:
            # Requesting another employee's data
            if self._is_own_data_only(requested_data):
                return AccessAttempt(
                    user_id=user_id,
                    user_role=user_role,
                    requested_data=requested_data,
                    target_employee_id=target_employee_id,
                    granted=False,
                    reason=f"Role '{user_role.value}' can only access own {requested_data.value}, not other employees'",
                    timestamp=datetime.now().isoformat()
                )
        
        # Access granted
        return AccessAttempt(
            user_id=user_id,
            user_role=user_role,
            requested_data=requested_data,
            target_employee_id=target_employee_id,
            granted=True,
            reason="Access granted based on role permissions",
            timestamp=datetime.now().isoformat()
        )
    
    def _is_own_data_only(self, data_category: DataCategory) -> bool:
        """Check if a data category is 'own data only'"""
        own_data_categories = {
            DataCategory.OWN_COMPENSATION,
            DataCategory.OWN_BENEFITS,
            DataCategory.OWN_SCHEDULE,
            DataCategory.OWN_CREDENTIALS,
            DataCategory.OWN_PERFORMANCE
        }
        return data_category in own_data_categories
    
    def get_accessible_data_for_role(self, role: UserRole) -> List[str]:
        """Get list of accessible data categories for a role"""
        permissions = self.role_permissions.get(role, set())
        return [category.value for category in permissions]


# Test the RBAC system
if __name__ == "__main__":
    print("🧪 Testing RBAC System\n")
    
    rbac = RoleManager()
    
    print("="*60)
    print("Test 1: Your Phase 4 Scenario")
    print("Nurse requests Dr. Chen's salary")
    print("="*60)
    
    # Nurse tries to access another employee's compensation
    attempt = rbac.check_access(
        user_id="EMP-NURSE-001",
        user_role=UserRole.NURSE,
        requested_data=DataCategory.OWN_COMPENSATION,
        target_employee_id="EMP-PHYSICIAN-042"  # Dr. Chen
    )
    
    print(f"User: Nurse (EMP-NURSE-001)")
    print(f"Request: Compensation data for EMP-PHYSICIAN-042 (Dr. Chen)")
    print(f"Result: {'✅ GRANTED' if attempt.granted else '❌ DENIED'}")
    print(f"Reason: {attempt.reason}")
    print()
    
    print("="*60)
    print("Test 2: Nurse Requests Own Salary")
    print("="*60)
    
    # Nurse accesses own compensation
    attempt = rbac.check_access(
        user_id="EMP-NURSE-001",
        user_role=UserRole.NURSE,
        requested_data=DataCategory.OWN_COMPENSATION,
        target_employee_id="EMP-NURSE-001"  # Own data
    )
    
    print(f"User: Nurse (EMP-NURSE-001)")
    print(f"Request: Own compensation data")
    print(f"Result: {'✅ GRANTED' if attempt.granted else '❌ DENIED'}")
    print(f"Reason: {attempt.reason}")
    print()
    
    print("="*60)
    print("Test 3: HR Admin Requests Dr. Chen's Salary")
    print("="*60)
    
    # HR Admin accesses any employee's compensation
    attempt = rbac.check_access(
        user_id="EMP-HR-ADMIN-005",
        user_role=UserRole.HR_ADMIN,
        requested_data=DataCategory.ALL_COMPENSATION,
        target_employee_id="EMP-PHYSICIAN-042"  # Dr. Chen
    )
    
    print(f"User: HR Admin (EMP-HR-ADMIN-005)")
    print(f"Request: Compensation data for EMP-PHYSICIAN-042 (Dr. Chen)")
    print(f"Result: {'✅ GRANTED' if attempt.granted else '❌ DENIED'}")
    print(f"Reason: {attempt.reason}")
    print()
    
    print("="*60)
    print("Test 4: Physician Requests License Verification Access")
    print("="*60)
    
    # Physician tries to access license verification (compliance-only)
    attempt = rbac.check_access(
        user_id="EMP-PHYSICIAN-042",
        user_role=UserRole.PHYSICIAN,
        requested_data=DataCategory.LICENSE_VERIFICATION
    )
    
    print(f"User: Physician (EMP-PHYSICIAN-042)")
    print(f"Request: License verification access")
    print(f"Result: {'✅ GRANTED' if attempt.granted else '❌ DENIED'}")
    print(f"Reason: {attempt.reason}")
    print()
    
    print("="*60)
    print("Test 5: Role Permission Summary")
    print("="*60)
    
    for role in [UserRole.NURSE, UserRole.HR_ADMIN, UserRole.FINANCE]:
        permissions = rbac.get_accessible_data_for_role(role)
        print(f"\n{role.value.upper()}:")
        for perm in permissions:
            print(f"  ✓ {perm}")