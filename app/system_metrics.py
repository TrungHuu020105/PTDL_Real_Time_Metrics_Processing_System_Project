"""
System metrics collector for real CPU and RAM usage.
Uses psutil to monitor actual system performance.
"""

import psutil
import platform
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from app.schemas import MetricCreate
from app.crud import create_metric
from sqlalchemy.orm import Session


class SystemMetricsCollector:
    """Collects real-time system metrics from the machine."""

    @staticmethod
    def get_cpu_percent(interval: float = 1.0) -> float:
        """
        Get current CPU usage percentage.
        
        Args:
            interval: Measurement interval in seconds (default: 1.0)
            
        Returns:
            CPU usage as percentage (0-100)
        """
        return psutil.cpu_percent(interval=interval)

    @staticmethod
    def get_memory_percent() -> float:
        """
        Get current memory (RAM) usage percentage.
        
        Returns:
            Memory usage as percentage (0-100)
        """
        memory_info = psutil.virtual_memory()
        return memory_info.percent

    @staticmethod
    def get_system_metrics() -> Dict[str, float]:
        """
        Get all system metrics at once.
        
        Returns:
            Dictionary with cpu and memory percentages
        """
        return {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent
        }

    @staticmethod
    def get_detailed_metrics() -> Dict[str, Any]:
        """
        Get detailed system information.
        
        Returns:
            Dictionary with comprehensive system metrics
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "per_core": psutil.cpu_percent(interval=0.1, percpu=True)
            },
            "memory": {
                "percent": memory_info.percent,
                "used": memory_info.used,
                "available": memory_info.available,
                "total": memory_info.total,
            },
            "disk": {
                "percent": disk_info.percent,
                "used": disk_info.used,
                "free": disk_info.free,
                "total": disk_info.total,
            },
            "timestamp": datetime.now(timezone(timedelta(hours=7))).isoformat()
        }

    @staticmethod
    def save_cpu_metric(db: Session, source: str = "system_monitor") -> Dict[str, Any]:
        """
        Measure and save current CPU usage to database.
        
        Args:
            db: Database session
            source: Data source identifier
            
        Returns:
            Created metric data
        """
        cpu_value = SystemMetricsCollector.get_cpu_percent(interval=0.5)
        
        metric = MetricCreate(
            metric_type="cpu",
            value=cpu_value,
            source=source,
            timestamp=None  # Use current time
        )
        
        created = create_metric(db, metric)
        return {
            "metric_type": "cpu",
            "value": cpu_value,
            "source": source,
            "timestamp": created.timestamp.isoformat()
        }

    @staticmethod
    def save_memory_metric(db: Session, source: str = "system_monitor") -> Dict[str, Any]:
        """
        Measure and save current memory usage to database.
        
        Args:
            db: Database session
            source: Data source identifier
            
        Returns:
            Created metric data
        """
        memory_value = SystemMetricsCollector.get_memory_percent()
        
        metric = MetricCreate(
            metric_type="memory",
            value=memory_value,
            source=source,
            timestamp=None  # Use current time
        )
        
        created = create_metric(db, metric)
        return {
            "metric_type": "memory",
            "value": memory_value,
            "source": source,
            "timestamp": created.timestamp.isoformat()
        }

    @staticmethod
    def save_system_metrics(db: Session, source: str = "system_monitor") -> Dict[str, Any]:
        """
        Measure and save both CPU and memory metrics to database.
        
        Args:
            db: Database session
            source: Data source identifier
            
        Returns:
            Dictionary with both metrics
        """
        cpu_value = SystemMetricsCollector.get_cpu_percent(interval=0.1)
        memory_value = SystemMetricsCollector.get_memory_percent()
        vietnam_tz = timezone(timedelta(hours=7))
        timestamp = datetime.now(vietnam_tz)
        
        # Create CPU metric
        cpu_metric = MetricCreate(
            metric_type="cpu",
            value=cpu_value,
            source=source,
            timestamp=timestamp
        )
        cpu_created = create_metric(db, cpu_metric)
        
        # Create memory metric
        memory_metric = MetricCreate(
            metric_type="memory",
            value=memory_value,
            source=source,
            timestamp=timestamp
        )
        memory_created = create_metric(db, memory_metric)
        
        return {
            "timestamp": timestamp.isoformat(),
            "source": source,
            "metrics": {
                "cpu": {
                    "value": cpu_value,
                    "percent": cpu_value
                },
                "memory": {
                    "value": memory_value,
                    "percent": memory_value
                }
            }
        }

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Get system hardware information.
        
        Returns:
            Dictionary with CPU cores, RAM (GB), and OS type
        """
        cpu_count_physical = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 1
        ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        os_type = platform.system()
        
        return {
            "cpu_cores": cpu_count_physical,
            "ram_gb": ram_total_gb,
            "os_type": os_type
        }
