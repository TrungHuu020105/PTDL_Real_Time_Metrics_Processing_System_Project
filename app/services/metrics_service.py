"""Business logic for metrics processing and aggregation"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Metric
from app import crud


class MetricsService:
    """Service for metrics processing and aggregation"""

    @staticmethod
    def calculate_average(metrics: List[Metric]) -> Optional[float]:
        """Calculate average value from metrics"""
        if not metrics:
            return None
        return sum(m.value for m in metrics) / len(metrics)

    @staticmethod
    def calculate_total(metrics: List[Metric]) -> float:
        """Calculate total value from metrics"""
        if not metrics:
            return 0.0
        return sum(m.value for m in metrics)

    @staticmethod
    def get_aggregated_summary(db: Session, minutes: int = 1) -> Dict[str, Any]:
        """
        Get aggregated metrics summary for specified time range.
        
        Returns dict with:
        - avg_cpu_1m: Average CPU usage
        - avg_memory_1m: Average memory usage
        - latest_cpu: Latest CPU value
        - latest_memory: Latest memory value
        - timestamp: Timestamp of calculation
        """
        # Get all metrics in range
        cpu_metrics, memory_metrics = crud.get_all_metrics_in_range(
            db, minutes
        )

        # Get latest values
        latest_cpu, latest_memory = crud.get_latest_metrics(db)

        # Calculate aggregations
        avg_cpu = MetricsService.calculate_average(cpu_metrics)
        avg_memory = MetricsService.calculate_average(memory_metrics)

        return {
            "avg_cpu_1m": avg_cpu,
            "avg_memory_1m": avg_memory,
            "latest_cpu": latest_cpu.value if latest_cpu else None,
            "latest_memory": latest_memory.value if latest_memory else None,
            "timestamp": datetime.now(timezone(timedelta(hours=7)))
        }

    @staticmethod
    def get_latest_values(db: Session) -> Dict[str, Any]:
        """
        Get latest values for all metric types.
        
        Returns dict with latest values and timestamp.
        """
        latest_cpu, latest_memory = crud.get_latest_metrics(db)

        return {
            "latest_cpu": latest_cpu.value if latest_cpu else None,
            "latest_memory": latest_memory.value if latest_memory else None,
            "timestamp": datetime.now(timezone(timedelta(hours=7)))
        }
