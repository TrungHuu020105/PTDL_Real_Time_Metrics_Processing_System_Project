"""
Script to generate fake IoT sensor data and save to database.
Run this once to populate the database with realistic IoT metrics.

Usage:
    python generate_iot_data.py
"""

import random
import sys
from datetime import datetime, timedelta

# Add app directory to path
sys.path.insert(0, '.')

from app.schemas import MetricCreate, MetricBulkCreate
from app.crud import create_metrics_bulk
from app.database import SessionLocal, init_db


def generate_iot_data(count: int = 200) -> dict:
    """
    Generate realistic IoT sensor data.
    
    Args:
        count: Number of IoT metrics to generate (default: 200)
    
    Returns:
        Dictionary with generation stats
    """
    
    # Initialize database
    init_db()
    
    # IoT metric types with their realistic ranges
    iot_metrics = {
        "temperature": {
            "unit": "°C",
            "min": 15,
            "max": 35,
            "description": "Temperature"
        },
        "humidity": {
            "unit": "%",
            "min": 30,
            "max": 90,
            "description": "Humidity"
        },
        "soil_moisture": {
            "unit": "%",
            "min": 0,
            "max": 100,
            "description": "Soil Moisture"
        },
        "light_intensity": {
            "unit": "lux",
            "min": 0,
            "max": 1000,
            "description": "Light Intensity"
        },
        "pressure": {
            "unit": "hPa",
            "min": 900,
            "max": 1100,
            "description": "Atmospheric Pressure"
        }
    }
    
    # Sensor sources
    sensor_sources = [f"sensor_{i}" for i in range(1, 5)]  # sensor_1, sensor_2, sensor_3, sensor_4
    
    metrics_to_create = []
    stats = {
        "total": 0,
        "by_type": {},
        "by_source": {}
    }
    
    print("=" * 70)
    print("🚀 GENERATING FAKE IoT SENSOR DATA")
    print("=" * 70)
    print(f"📊 Generating {count} IoT metrics...")
    print(f"📡 Sensors: {sensor_sources}")
    print(f"📈 Metric types: {list(iot_metrics.keys())}")
    print()
    
    # Generate sample data
    for i in range(count):
        # Random metric type
        metric_type = random.choice(list(iot_metrics.keys()))
        metric_info = iot_metrics[metric_type]
        
        # Generate realistic value
        value = round(random.uniform(metric_info["min"], metric_info["max"]), 2)
        
        # Random source
        source = random.choice(sensor_sources)
        
        # No timestamp - will use current time
        metric = MetricCreate(
            metric_type=metric_type,
            value=value,
            source=source,
            timestamp=None
        )
        metrics_to_create.append(metric)
        
        # Track stats
        stats["total"] += 1
        stats["by_type"][metric_type] = stats["by_type"].get(metric_type, 0) + 1
        stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
    
    # Create bulk record
    bulk_data = MetricBulkCreate(metrics=metrics_to_create)
    
    # Get database session and save
    db = SessionLocal()
    try:
        created_metrics = create_metrics_bulk(db, bulk_data.metrics)
        print("✅ SUCCESS! Data saved to database.")
        print(f"📥 Created {len(created_metrics)} IoT metrics")
        print()
        
        # Print statistics
        print("📊 STATISTICS:")
        print("-" * 70)
        print(f"  Total metrics created: {stats['total']}")
        print()
        
        print("  By Metric Type:")
        for metric_type, count in sorted(stats["by_type"].items()):
            unit = iot_metrics[metric_type]["unit"]
            percentage = (count / stats["total"]) * 100
            print(f"    • {metric_type:20} {count:3} records ({percentage:5.1f}%) [{unit}]")
        print()
        
        print("  By Sensor Source:")
        for source, count in sorted(stats["by_source"].items()):
            percentage = (count / stats["total"]) * 100
            print(f"    • {source:20} {count:3} records ({percentage:5.1f}%)")
        print()
        
        # Print sample data
        print("📋 SAMPLE DATA (First 5 records):")
        print("-" * 70)
        for i, metric in enumerate(created_metrics[:5], 1):
            unit = iot_metrics[metric.metric_type]["unit"]
            print(f"  {i}. {metric.metric_type:20} = {metric.value:8.2f} {unit:5} | {metric.source:10} | {metric.timestamp}")
        print()
        
        print("=" * 70)
        print("🎉 Ready to use! Test with:")
        print("   curl \"http://localhost:8000/api/metrics/history?metric_type=temperature&minutes=60\"")
        print("=" * 70)
        
        return {
            "success": True,
            "created": len(created_metrics),
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def generate_iot_data_spread_time(count: int = 200, hours: int = 24) -> dict:
    """
    Generate IoT data spread over a time range.
    
    Args:
        count: Number of metrics to generate
        hours: Spread data over how many hours (default: 24)
    
    Returns:
        Dictionary with generation stats
    """
    
    # Initialize database
    init_db()
    
    iot_metrics = {
        "temperature": {"min": 15, "max": 35},
        "humidity": {"min": 30, "max": 90},
        "soil_moisture": {"min": 0, "max": 100},
        "light_intensity": {"min": 0, "max": 1000},
        "pressure": {"min": 900, "max": 1100}
    }
    
    sensor_sources = [f"sensor_{i}" for i in range(1, 5)]
    metrics_to_create = []
    
    print("=" * 70)
    print("🚀 GENERATING FAKE IoT SENSOR DATA (Time-Spread)")
    print("=" * 70)
    print(f"📊 Generating {count} IoT metrics spread over {hours} hours...")
    print()
    
    now = datetime.utcnow()
    
    # Generate sample data
    for i in range(count):
        metric_type = random.choice(list(iot_metrics.keys()))
        metric_info = iot_metrics[metric_type]
        value = round(random.uniform(metric_info["min"], metric_info["max"]), 2)
        source = random.choice(sensor_sources)
        
        # Spread timestamps over the specified hours
        seconds_ago = random.randint(0, hours * 3600)
        timestamp = now - timedelta(seconds=seconds_ago)
        
        metric = MetricCreate(
            metric_type=metric_type,
            value=value,
            source=source,
            timestamp=timestamp
        )
        metrics_to_create.append(metric)
    
    # Create bulk record
    bulk_data = MetricBulkCreate(metrics=metrics_to_create)
    
    # Get database session and save
    db = SessionLocal()
    try:
        created_metrics = create_metrics_bulk(db, bulk_data.metrics)
        print(f"✅ SUCCESS! Created {len(created_metrics)} IoT metrics")
        print()
        print("=" * 70)
        print("🎉 Data ready! Test with:")
        print(f"   curl \"http://localhost:8000/api/metrics/history?metric_type=temperature&minutes={hours*60}\"")
        print("=" * 70)
        
        return {
            "success": True,
            "created": len(created_metrics)
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate fake IoT sensor data")
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="Number of metrics to generate (default: 200)"
    )
    parser.add_argument(
        "--spread-hours",
        type=int,
        default=None,
        help="Spread data over N hours (optional)"
    )
    
    args = parser.parse_args()
    
    if args.spread_hours:
        result = generate_iot_data_spread_time(count=args.count, hours=args.spread_hours)
    else:
        result = generate_iot_data(count=args.count)
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)
