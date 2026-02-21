"""
ROI Calculator for CareOps AI Platform
Calculates return on investment and total cost of ownership
"""

from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json


# @dataclass
# class ManualProcessCosts:
#     """Current manual process costs (before AI)"""
    
#     # Labor costs
#     fte_count: float  # Full-time equivalents
#     annual_salary_per_fte: float
#     benefits_multiplier: float = 1.3  # 30% benefits overhead
    
#     # Time metrics
#     hours_per_week: float
#     weeks_per_year: int = 50  # Account for vacation
    
#     # Error costs
#     error_rate: float  # Percentage (e.g., 0.03 = 3%)
#     cost_per_error: float  # Compliance penalties, rework
    
#     # Opportunity costs
#     staff_time_saved_hours_per_month: float = 0
@dataclass
class ManualProcessCosts:
    """Current manual process costs (before AI)"""
    
    # Labor costs (required fields first)
    fte_count: float  # Full-time equivalents
    annual_salary_per_fte: float
    hours_per_week: float
    error_rate: float  # Percentage (e.g., 0.03 = 3%)
    cost_per_error: float  # Compliance penalties, rework
    
    # Fields with defaults (must come last)
    benefits_multiplier: float = 1.3  # 30% benefits overhead
    weeks_per_year: int = 50  # Account for vacation
    staff_time_saved_hours_per_month: float = 0

@dataclass
class AISystemCosts:
    """AI system costs"""
    
    # Development costs (one-time)
    development_hours: float
    developer_hourly_rate: float
    
    # Azure costs (recurring)
    monthly_azure_compute: float  # AI Foundry, VMs
    monthly_azure_storage: float  # Blob, Cosmos DB
    monthly_model_api_cost: float  # GPT-4o token usage
    
    # Maintenance costs (recurring)
    monthly_support_hours: float
    support_hourly_rate: float


class ROICalculator:
    """
    Calculate ROI and TCO for AI implementation
    
    Provides CFO-ready financial analysis
    """
    
    def __init__(
        self,
        manual_costs: ManualProcessCosts,
        ai_costs: AISystemCosts
    ):
        """
        Initialize ROI calculator
        
        Args:
            manual_costs: Current manual process costs
            ai_costs: AI system costs
        """
        self.manual_costs = manual_costs
        self.ai_costs = ai_costs
    
    def calculate_manual_annual_cost(self) -> float:
        """Calculate total annual cost of manual process"""
        
        # Labor costs
        base_labor = (
            self.manual_costs.fte_count *
            self.manual_costs.annual_salary_per_fte *
            self.manual_costs.benefits_multiplier
        )
        
        # Error costs
        annual_hours = (
            self.manual_costs.hours_per_week *
            self.manual_costs.weeks_per_year
        )
        
        # Estimate number of transactions
        # Assuming 1 transaction per 15 minutes average
        estimated_transactions = (annual_hours * 60) / 15
        
        error_costs = (
            estimated_transactions *
            self.manual_costs.error_rate *
            self.manual_costs.cost_per_error
        )
        
        return base_labor + error_costs
    
    def calculate_ai_first_year_cost(self) -> float:
        """Calculate total first-year AI cost (including development)"""
        
        # One-time development
        development_cost = (
            self.ai_costs.development_hours *
            self.ai_costs.developer_hourly_rate
        )
        
        # Recurring annual costs
        recurring_annual = self.calculate_ai_recurring_annual_cost()
        
        return development_cost + recurring_annual
    
    def calculate_ai_recurring_annual_cost(self) -> float:
        """Calculate recurring annual AI costs"""
        
        monthly_costs = (
            self.ai_costs.monthly_azure_compute +
            self.ai_costs.monthly_azure_storage +
            self.ai_costs.monthly_model_api_cost +
            (self.ai_costs.monthly_support_hours * self.ai_costs.support_hourly_rate)
        )
        
        return monthly_costs * 12
    
    def calculate_annual_savings(self, year: int = 1) -> float:
        """
        Calculate annual savings
        
        Args:
            year: Which year (1, 2, 3, etc.)
            
        Returns:
            Net savings for that year
        """
        
        manual_cost = self.calculate_manual_annual_cost()
        
        if year == 1:
            ai_cost = self.calculate_ai_first_year_cost()
        else:
            ai_cost = self.calculate_ai_recurring_annual_cost()
        
        return manual_cost - ai_cost
    
    def calculate_payback_period_months(self) -> float:
        """
        Calculate payback period in months
        
        Returns:
            Months to break even
        """
        
        development_cost = (
            self.ai_costs.development_hours *
            self.ai_costs.developer_hourly_rate
        )
        
        monthly_manual = self.calculate_manual_annual_cost() / 12
        monthly_ai = self.calculate_ai_recurring_annual_cost() / 12
        monthly_savings = monthly_manual - monthly_ai
        
        if monthly_savings <= 0:
            return float('inf')  # Never pays back
        
        return development_cost / monthly_savings
    
    def calculate_3_year_roi(self) -> float:
        """
        Calculate 3-year ROI percentage
        
        Returns:
            ROI as percentage (e.g., 250.0 = 250% return)
        """
        
        total_investment = self.calculate_ai_first_year_cost()
        
        total_savings = sum(
            self.calculate_annual_savings(year)
            for year in range(1, 4)
        )
        
        if total_investment <= 0:
            return 0
        
        roi = ((total_savings - total_investment) / total_investment) * 100
        
        return roi
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """
        Generate executive summary for CFO/board
        
        Returns:
            Comprehensive ROI analysis
        """
        
        manual_annual = self.calculate_manual_annual_cost()
        ai_year1 = self.calculate_ai_first_year_cost()
        ai_recurring = self.calculate_ai_recurring_annual_cost()
        
        year1_savings = self.calculate_annual_savings(1)
        year2_savings = self.calculate_annual_savings(2)
        year3_savings = self.calculate_annual_savings(3)
        
        three_year_total = year1_savings + year2_savings + year3_savings
        
        payback_months = self.calculate_payback_period_months()
        roi_3year = self.calculate_3_year_roi()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "executive_summary": {
                "recommendation": "APPROVE" if roi_3year > 100 else "REVIEW",
                "3_year_roi": f"{roi_3year:.1f}%",
                "payback_period": f"{payback_months:.1f} months",
                "3_year_total_savings": f"${three_year_total:,.0f}",
                "year1_net": "Positive" if year1_savings > 0 else "Negative"
            },
            "current_state": {
                "annual_cost": f"${manual_annual:,.0f}",
                "fte_count": self.manual_costs.fte_count,
                "error_rate": f"{self.manual_costs.error_rate*100:.1f}%",
                "breakdown": "Labor + Error Costs + Opportunity Costs"
            },
            "ai_implementation": {
                "year1_total_cost": f"${ai_year1:,.0f}",
                "development_cost": f"${self.ai_costs.development_hours * self.ai_costs.developer_hourly_rate:,.0f}",
                "recurring_annual_cost": f"${ai_recurring:,.0f}",
                "monthly_run_rate": f"${ai_recurring/12:,.0f}"
            },
            "financial_impact": {
                "year1_savings": f"${year1_savings:,.0f}",
                "year2_savings": f"${year2_savings:,.0f}",
                "year3_savings": f"${year3_savings:,.0f}",
                "3_year_total_savings": f"${three_year_total:,.0f}"
            },
            "key_metrics": {
                "payback_period_months": round(payback_months, 1),
                "3_year_roi_percentage": round(roi_3year, 1),
                "annual_savings_after_payback": f"${ai_recurring:,.0f}",
                "cost_reduction_percentage": round((1 - (ai_recurring / manual_annual)) * 100, 1)
            }
        }


# Test with CareOps actual numbers
if __name__ == "__main__":
    print("🧪 Testing ROI Calculator — CareOps Scenario\n")
    
    print("="*60)
    print("Current State: Manual Credentialing Process")
    print("="*60)
    print()
    
    # Real CareOps numbers from Phase 2
    manual = ManualProcessCosts(
        fte_count=2.0,  # 2 FTE credentialing staff
        annual_salary_per_fte=65_000,
        benefits_multiplier=1.3,
        hours_per_week=40,
        weeks_per_year=50,
        error_rate=0.035,  # 3.5% error rate
        cost_per_error=5_000,  # Compliance penalties, rework
        staff_time_saved_hours_per_month=68  # From Phase 0
    )
    
    print(f"Credentialing Staff: {manual.fte_count} FTE")
    print(f"Annual Salary: ${manual.annual_salary_per_fte:,} per FTE")
    print(f"Benefits Overhead: {(manual.benefits_multiplier-1)*100:.0f}%")
    print(f"Error Rate: {manual.error_rate*100:.1f}%")
    print(f"Cost Per Error: ${manual.cost_per_error:,}")
    print()
    
    print("="*60)
    print("AI Implementation Costs")
    print("="*60)
    print()
    
    # AI system costs
    ai = AISystemCosts(
        development_hours=160,  # ~4 weeks of development
        developer_hourly_rate=150,
        monthly_azure_compute=50,  # AI Foundry
        monthly_azure_storage=10,  # Blob + Cosmos
        monthly_model_api_cost=25,  # Token usage (with caching!)
        monthly_support_hours=10,  # Ongoing maintenance
        support_hourly_rate=120
    )
    
    print(f"Development: {ai.development_hours} hours @ ${ai.developer_hourly_rate}/hr")
    print(f"Azure Compute: ${ai.monthly_azure_compute}/month")
    print(f"Model API (with caching): ${ai.monthly_model_api_cost}/month")
    print(f"Support: {ai.monthly_support_hours} hrs/month @ ${ai.support_hourly_rate}/hr")
    print()
    
    # Calculate ROI
    calculator = ROICalculator(manual, ai)
    
    print("="*60)
    print("Executive Summary")
    print("="*60)
    print()
    
    summary = calculator.generate_executive_summary()
    print(json.dumps(summary, indent=2))
    
    print("\n" + "="*60)
    print("✅ ROI Calculation Complete")
    print("="*60)