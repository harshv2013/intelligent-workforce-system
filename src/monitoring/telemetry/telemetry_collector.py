"""
Telemetry Collector for Agent Performance Monitoring
Tracks every agent action for observability and optimization
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


class MetricType(Enum):
    """Types of metrics to track"""
    AGENT_QUERY = "agent_query"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    MODEL_INFERENCE = "model_inference"
    A2A_MESSAGE = "a2a_message"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


@dataclass
class TelemetryEvent:
    """
    Single telemetry event
    
    Captures everything needed for performance analysis and debugging
    """
    
    # Core fields
    timestamp: str
    event_id: str
    metric_type: MetricType
    
    # Agent context
    agent_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    
    # Success tracking
    success: bool = True
    error_message: Optional[str] = None
    
    # Additional context
    details: Dict[str, Any] = None
    
    # Model details (for AI calls)
    model_name: Optional[str] = None
    deployment_name: Optional[str] = None
    
    # Resource usage
    api_calls: int = 0
    cache_hit: bool = False


class TelemetryCollector:
    """
    Centralized telemetry collection system
    
    In production, this would send to Azure Monitor / Application Insights
    For development, we store in local files with in-memory aggregation
    """
    
    def __init__(self, metrics_directory: str = "data/metrics"):
        """
        Initialize telemetry collector
        
        Args:
            metrics_directory: Where to store metrics
        """
        self.metrics_directory = Path(metrics_directory)
        self.metrics_directory.mkdir(parents=True, exist_ok=True)
        
        # In-memory metrics for real-time dashboards
        self.recent_events = []
        self.max_recent_events = 1000
        
        # Aggregated metrics
        self.agent_stats = {}
    
    def track(
        self,
        metric_type: MetricType,
        agent_id: str,
        duration_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        cache_hit: bool = False
    ) -> TelemetryEvent:
        """
        Track a telemetry event
        
        Args:
            metric_type: Type of metric
            agent_id: Which agent
            duration_ms: How long it took
            tokens_used: Token count
            cost_usd: Cost in USD
            success: Whether it succeeded
            error_message: Error if failed
            user_id: User who triggered it
            session_id: Session identifier
            details: Additional context
            model_name: Model used
            cache_hit: Whether cache was used
            
        Returns:
            TelemetryEvent object
        """
        
        import uuid
        
        event = TelemetryEvent(
            timestamp=datetime.now().isoformat(),
            event_id=str(uuid.uuid4()),
            metric_type=metric_type,
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            success=success,
            error_message=error_message,
            details=details or {},
            model_name=model_name,
            cache_hit=cache_hit
        )
        
        # Store in recent events (circular buffer)
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
        
        # Update aggregated stats
        self._update_stats(event)
        
        # Write to file
        self._write_to_file(event)
        
        return event
    
    def _update_stats(self, event: TelemetryEvent):
        """Update aggregated statistics"""
        
        if event.agent_id not in self.agent_stats:
            self.agent_stats[event.agent_id] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration_ms": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "durations": [],
                "cache_hits": 0,
                "cache_misses": 0
            }
        
        stats = self.agent_stats[event.agent_id]
        stats["total_calls"] += 1
        
        if event.success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        if event.duration_ms:
            stats["total_duration_ms"] += event.duration_ms
            stats["durations"].append(event.duration_ms)
        
        if event.tokens_used:
            stats["total_tokens"] += event.tokens_used
        
        if event.cost_usd:
            stats["total_cost_usd"] += event.cost_usd
        
        if event.cache_hit:
            stats["cache_hits"] += 1
        else:
            stats["cache_misses"] += 1
    
    def _write_to_file(self, event: TelemetryEvent):
        """Write event to JSONL file"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        metrics_file = self.metrics_directory / f"metrics_{today}.jsonl"
        
        # Convert to dict
        event_dict = asdict(event)
        event_dict['metric_type'] = event.metric_type.value
        
        # Append to file
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(event_dict) + '\n')
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for an agent
        
        Args:
            agent_id: Agent to get stats for
            
        Returns:
            Statistics dictionary
        """
        
        if agent_id not in self.agent_stats:
            return {}
        
        stats = self.agent_stats[agent_id].copy()
        
        # Calculate averages
        if stats["total_calls"] > 0:
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_calls"]
            stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_calls"]
        
        # Calculate percentiles
        if stats["durations"]:
            stats["p50_duration_ms"] = statistics.median(stats["durations"])
            stats["p95_duration_ms"] = statistics.quantiles(stats["durations"], n=20)[18] if len(stats["durations"]) >= 20 else max(stats["durations"])
            stats["p99_duration_ms"] = statistics.quantiles(stats["durations"], n=100)[98] if len(stats["durations"]) >= 100 else max(stats["durations"])
        
        return stats
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents"""
        
        return {
            agent_id: self.get_agent_stats(agent_id)
            for agent_id in self.agent_stats.keys()
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Performance report with key metrics
        """
        
        all_stats = self.get_all_stats()
        
        total_calls = sum(s.get("total_calls", 0) for s in all_stats.values())
        total_tokens = sum(s.get("total_tokens", 0) for s in all_stats.values())
        total_cost = sum(s.get("total_cost_usd", 0) for s in all_stats.values())
        
        # Find slowest agent
        slowest_agent = None
        slowest_avg = 0
        for agent_id, stats in all_stats.items():
            if stats.get("avg_duration_ms", 0) > slowest_avg:
                slowest_avg = stats["avg_duration_ms"]
                slowest_agent = agent_id
        
        # Find most expensive agent
        most_expensive_agent = None
        highest_cost = 0
        for agent_id, stats in all_stats.items():
            if stats.get("total_cost_usd", 0) > highest_cost:
                highest_cost = stats["total_cost_usd"]
                most_expensive_agent = agent_id
        
        return {
            "report_generated_at": datetime.now().isoformat(),
            "summary": {
                "total_api_calls": total_calls,
                "total_tokens_used": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "agents_monitored": len(all_stats)
            },
            "insights": {
                "slowest_agent": {
                    "agent_id": slowest_agent,
                    "avg_duration_ms": round(slowest_avg, 2)
                },
                "most_expensive_agent": {
                    "agent_id": most_expensive_agent,
                    "total_cost_usd": round(highest_cost, 4)
                }
            },
            "agent_stats": all_stats
        }


# Test the telemetry collector
if __name__ == "__main__":
    print("🧪 Testing Telemetry Collector\n")
    
    collector = TelemetryCollector()
    
    print("="*60)
    print("Simulating Agent Activity")
    print("="*60)
    print()
    
    # Simulate HR Agent activity
    for i in range(5):
        collector.track(
            metric_type=MetricType.AGENT_QUERY,
            agent_id="hr-agent",
            duration_ms=1200 + (i * 100),
            tokens_used=1500 + (i * 50),
            cost_usd=0.0045 + (i * 0.0001),
            success=True,
            model_name="gpt-4o",
            user_id=f"EMP-{i:03d}"
        )
    
    print("✓ Tracked 5 HR Agent queries")
    
    # Simulate Credentialing Agent with cache (your Phase 5 decision!)
    for i in range(10):
        # 70% cache hit rate (as per your optimization)
        cache_hit = i < 7
        duration = 1800 if not cache_hit else 600  # Cached is faster!
        
        collector.track(
            metric_type=MetricType.TOOL_CALL,
            agent_id="credentialing-agent",
            duration_ms=duration,
            tokens_used=800 if not cache_hit else 200,
            cost_usd=0.002 if not cache_hit else 0.0005,
            success=True,
            cache_hit=cache_hit,
            details={"tool": "verify_license", "cached": cache_hit}
        )
    
    print("✓ Tracked 10 Credentialing Agent calls (70% cache hits)")
    
    # Simulate one failure
    collector.track(
        metric_type=MetricType.AGENT_QUERY,
        agent_id="credentialing-agent",
        duration_ms=5000,
        success=False,
        error_message="External API timeout",
        details={"api": "state_medical_board"}
    )
    
    print("✓ Tracked 1 API failure")
    
    print("\n" + "="*60)
    print("Agent Statistics")
    print("="*60)
    print()
    
    # Get stats for each agent
    for agent_id in ["hr-agent", "credentialing-agent"]:
        stats = collector.get_agent_stats(agent_id)
        
        print(f"{agent_id.upper()}:")
        print(f"  Total Calls: {stats.get('total_calls', 0)}")
        print(f"  Success Rate: {stats.get('success_rate', 0)*100:.1f}%")
        print(f"  Avg Duration: {stats.get('avg_duration_ms', 0):.1f}ms")
        print(f"  P95 Duration: {stats.get('p95_duration_ms', 0):.1f}ms")
        print(f"  Cache Hit Rate: {stats.get('cache_hit_rate', 0)*100:.1f}%")
        print(f"  Total Tokens: {stats.get('total_tokens', 0):,}")
        print(f"  Total Cost: ${stats.get('total_cost_usd', 0):.4f}")
        print()
    
    print("="*60)
    print("Performance Report")
    print("="*60)
    print()
    
    report = collector.generate_performance_report()
    print(json.dumps(report, indent=2))
    
    print("\n" + "="*60)
    print("✅ Telemetry Collection Tests Complete")
    print("="*60)