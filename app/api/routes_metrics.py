"""API routes for metrics endpoints"""

from typing import List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    MetricCreate,
    MetricBulkCreate,
    MetricResponse,
    LatestMetricsResponse,
    SummaryMetricsResponse,
    MetricsHistoryResponse,
    HealthResponse
)
from app import crud
from app.services.metrics_service import MetricsService
from app.system_metrics import SystemMetricsCollector

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Real-Time Metrics Processing System is running"
    }


@router.post("/metrics", response_model=MetricResponse, status_code=201)
async def create_metric(
    metric: MetricCreate,
    db: Session = Depends(get_db)
):
    """
    Create a single metric record.
    
    Example request body:
    {
        "metric_type": "cpu",
        "value": 45.5,
        "source": "server_1",
        "timestamp": "2024-04-04T10:30:00"  // optional
    }
    """
    db_metric = crud.create_metric(db, metric)
    return db_metric


@router.post("/metrics/bulk", response_model=List[MetricResponse], status_code=201)
async def create_metrics_bulk(
    bulk_data: MetricBulkCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple metric records at once.
    
    Example request body:
    {
        "metrics": [
            {"metric_type": "cpu", "value": 45.5, "source": "server_1"},
            {"metric_type": "memory", "value": 78.2, "source": "server_1"}
        ]
    }
    """
    db_metrics = crud.create_metrics_bulk(db, bulk_data.metrics)
    return db_metrics


@router.get("/metrics/latest", response_model=LatestMetricsResponse)
async def get_latest_metrics(db: Session = Depends(get_db)):
    """
    Get the latest value for each metric type (cpu, memory).
    
    Returns the most recent recorded value for each metric type,
    or null if no data exists for that metric.
    """
    latest_data = MetricsService.get_latest_values(db)
    return latest_data


@router.get("/metrics/history", response_model=MetricsHistoryResponse)
async def get_metrics_history(
    metric_type: str = Query(..., description="Type of metric: cpu, memory, temperature, humidity, soil_moisture, light_intensity, pressure"),
    minutes: int = Query(5, ge=1, le=1440, description="Time range in minutes (1-1440)"),
    db: Session = Depends(get_db)
):
    """
    Get historical data for a specific metric type.
    
    Query parameters:
    - metric_type: Required. One of: 
      - Server metrics: cpu, memory
      - IoT sensors: temperature, humidity, soil_moisture, light_intensity, pressure
    - minutes: Optional. Time range in minutes (default: 5, max: 1440)
    
    Returns data sorted by timestamp (ascending), suitable for chart display.
    """
    # Validate metric_type
    server_types = {"cpu", "memory"}
    iot_types = {"temperature", "humidity", "soil_moisture", "light_intensity", "pressure"}
    allowed_types = server_types | iot_types
    
    if metric_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric_type. Must be one of {allowed_types}"
        )

    metrics = crud.get_metrics_history(db, metric_type, minutes)

    return {
        "metric_type": metric_type,
        "data": metrics,
        "count": len(metrics)
    }


@router.get("/metrics/summary", response_model=SummaryMetricsResponse)
async def get_metrics_summary(
    minutes: int = Query(1, ge=1, le=1440, description="Time range in minutes (1-1440)"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated metrics summary for dashboard.
    
    Returns:
    - avg_cpu_1m: Average CPU usage over time range
    - avg_memory_1m: Average memory usage over time range
    - latest_cpu: Latest CPU value (not averaged)
    - latest_memory: Latest memory value (not averaged)
    
    Perfect for dashboard cards displaying KPIs.
    """
    summary = MetricsService.get_aggregated_summary(db, minutes)
    return summary


@router.post("/dev/generate-sample-data", status_code=201)
async def generate_sample_data(
    count: int = Query(50, ge=1, le=1000, description="Number of sample records to generate"),
    db: Session = Depends(get_db)
):
    """
    Generate sample metrics data for demo/testing purposes.
    
    This endpoint creates realistic sample metrics data with:
    - Random CPU values (30-95%)
    - Random Memory values (20-90%)
    - Random Request counts (100-5000)
    - Timestamps spread over the last hour
    - Multiple sources (server_1, server_2, server_3)
    """
    import random
    from datetime import timedelta

    metrics_to_create = []

    # Generate sample data
    for i in range(count):
        # Random timestamp within last hour
        minutes_ago = random.randint(0, 60)
        timestamp = None  # Will use current time in CRUD
        
        # Cycle through metric types and sources
        metric_type = random.choice(["cpu", "memory"])
        source = random.choice(["server_1", "server_2", "server_3"])

        # Generate realistic values
        if metric_type == "cpu":
            value = random.uniform(20, 95)
        else:  # memory
            value = random.uniform(15, 92)

        metric = MetricCreate(
            metric_type=metric_type,
            value=value,
            source=source,
            timestamp=timestamp
        )
        metrics_to_create.append(metric)

    # Create all metrics
    bulk_data = MetricBulkCreate(metrics=metrics_to_create)
    created_metrics = crud.create_metrics_bulk(db, bulk_data.metrics)

    return {
        "message": f"Successfully generated {len(created_metrics)} sample metrics",
        "count": len(created_metrics)
    }


@router.post("/dev/generate-iot-data", status_code=201)
async def generate_iot_data(
    count: int = Query(50, ge=1, le=1000, description="Number of IoT sample records to generate"),
    db: Session = Depends(get_db)
):
    """
    Generate fake IoT sensor data for demo/testing purposes.
    
    This endpoint creates realistic IoT metrics data with:
    - Temperature: 15-35°C
    - Humidity: 30-90%
    - Soil Moisture: 0-100%
    - Light Intensity: 0-1000 lux
    - Pressure: 900-1100 hPa
    - Multiple sources (sensor_1, sensor_2, sensor_3, sensor_4)
    
    Useful for testing IoT data pipeline integration.
    """
    import random

    metrics_to_create = []

    # IoT metric types and their realistic ranges
    iot_metrics = {
        "temperature": (15, 35),      # °C
        "humidity": (30, 90),         # %
        "soil_moisture": (0, 100),    # %
        "light_intensity": (0, 1000), # lux
        "pressure": (900, 1100)       # hPa
    }

    # Generate sample IoT data
    for i in range(count):
        # Random metric type and value range
        metric_type = random.choice(list(iot_metrics.keys()))
        min_val, max_val = iot_metrics[metric_type]
        
        # Generate realistic value
        if metric_type in ["temperature", "pressure"]:
            value = random.uniform(min_val, max_val)
        else:
            value = random.uniform(min_val, max_val)
        
        # IoT sensor sources
        source = random.choice([f"sensor_{i}" for i in range(1, 5)])

        metric = MetricCreate(
            metric_type=metric_type,
            value=value,
            source=source,
            timestamp=None  # Will use current time in CRUD
        )
        metrics_to_create.append(metric)

    # Create all metrics
    bulk_data = MetricBulkCreate(metrics=metrics_to_create)
    created_metrics = crud.create_metrics_bulk(db, bulk_data.metrics)

    return {
        "message": f"Successfully generated {len(created_metrics)} sample IoT metrics",
        "count": len(created_metrics),
        "iot_types": {
            "temperature": "Temperature in °C (15-35°C)",
            "humidity": "Humidity in % (30-90%)",
            "soil_moisture": "Soil Moisture in % (0-100%)",
            "light_intensity": "Light Intensity in lux (0-1000 lux)",
            "pressure": "Atmospheric Pressure in hPa (900-1100 hPa)"
        }
    }


# ==================== REAL SYSTEM METRICS ====================

@router.get("/system/current")
async def get_current_system_metrics():
    """
    Get real-time system metrics from the current machine.
    
    Returns:
    - cpu: Current CPU usage percentage (0-100%)
    - memory: Current RAM usage percentage (0-100%)
    - timestamp: Current timestamp
    - unit: Measurement unit
    
    This endpoint measures actual system performance in real-time.
    """
    metrics = SystemMetricsCollector.get_system_metrics()
    vietnam_tz = timezone(timedelta(hours=7))
    
    return {
        "timestamp": datetime.now(vietnam_tz).isoformat(),
        "metrics": {
            "cpu": {
                "value": round(metrics["cpu"], 2),
                "percent": round(metrics["cpu"], 2),
                "unit": "%"
            },
            "memory": {
                "value": round(metrics["memory"], 2),
                "percent": round(metrics["memory"], 2),
                "unit": "%"
            }
        }
    }


@router.get("/system/detailed")
async def get_detailed_system_metrics():
    """
    Get detailed system information including CPU cores, memory, and disk usage.
    
    Returns comprehensive system metrics including:
    - CPU: Usage percentage and per-core breakdown
    - Memory: Total, used, available in bytes
    - Disk: Usage on root partition
    """
    details = SystemMetricsCollector.get_detailed_metrics()
    
    return {
        "status": "success",
        "data": details
    }


@router.post("/system/collect", status_code=201)
async def collect_and_save_system_metrics(db: Session = Depends(get_db)):
    """
    Collect real-time system metrics and save to database.
    
    Measures current CPU and memory usage, then saves both metrics
    to the database with source="system_monitor".
    
    Returns:
    - timestamp: When metrics were collected
    - source: Data source (always "system_monitor")
    - metrics: Dict with cpu and memory values saved
    """
    result = SystemMetricsCollector.save_system_metrics(db, source="system_monitor")
    
    return {
        "message": "System metrics collected and saved",
        "timestamp": result["timestamp"],
        "source": result["source"],
        "metrics_saved": {
            "cpu": round(result["metrics"]["cpu"]["value"], 2),
            "memory": round(result["metrics"]["memory"]["value"], 2)
        }
    }


@router.post("/system/collect-cpu", status_code=201)
async def collect_cpu_only(db: Session = Depends(get_db)):
    """
    Collect and save only CPU metric to database.
    
    Returns the current CPU usage percentage.
    """
    result = SystemMetricsCollector.save_cpu_metric(db)
    
    return {
        "message": "CPU metric collected and saved",
        "metric_type": result["metric_type"],
        "value": round(result["value"], 2),
        "source": result["source"],
        "timestamp": result["timestamp"]
    }


@router.post("/system/collect-memory", status_code=201)
async def collect_memory_only(db: Session = Depends(get_db)):
    """
    Collect and save only memory metric to database.
    
    Returns the current memory usage percentage.
    """
    result = SystemMetricsCollector.save_memory_metric(db)
    
    return {
        "message": "Memory metric collected and saved",
        "metric_type": result["metric_type"],
        "value": round(result["value"], 2),
        "source": result["source"],
        "timestamp": result["timestamp"]
    }
