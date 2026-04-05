"""
Script to generate fake IoT sensor data and save to database.
Can run once or continuously (infinite loop).

Usage:
    python generate_iot_data.py                          # Run once
    python generate_iot_data.py --continuous             # Continuous mode (2s interval)
    python generate_iot_data.py --continuous --interval 5  # Continuous with 5s interval
"""

import random
import sys
import time
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


def generate_iot_data_continuous(count_per_batch: int = 50, interval: int = 2):
    """
    Generate fake IoT sensor data continuously (infinite loop).
    
    Args:
        count_per_batch: Number of metrics to generate per batch (default: 50)
        interval: Wait time between batches in seconds (default: 2)
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
    sensor_sources = [f"sensor_{i}" for i in range(1, 5)]
    
    print("=" * 70)
    print("🚀 CONTINUOUS IoT DATA GENERATOR (Fake Sensor Mode)")
    print("=" * 70)
    print(f"📊 Batch size: {count_per_batch} metrics per batch")
    print(f"⏱️  Interval: {interval} seconds")
    print(f"📡 Sensors: {sensor_sources}")
    print(f"📈 Metric types: {list(iot_metrics.keys())}")
    print()
    print("⚠️  Press Ctrl+C to stop\n")
    
    batch_count = 0
    total_created = 0
    
    try:
        while True:
            batch_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            metrics_to_create = []
            batch_stats = {
                "by_type": {},
                "by_source": {}
            }
            
            # Generate batch
            for i in range(count_per_batch):
                metric_type = random.choice(list(iot_metrics.keys()))
                metric_info = iot_metrics[metric_type]
                value = round(random.uniform(metric_info["min"], metric_info["max"]), 2)
                source = random.choice(sensor_sources)
                
                metric = MetricCreate(
                    metric_type=metric_type,
                    value=value,
                    source=source,
                    timestamp=None
                )
                metrics_to_create.append(metric)
                
                # Track stats
                batch_stats["by_type"][metric_type] = batch_stats["by_type"].get(metric_type, 0) + 1
                batch_stats["by_source"][source] = batch_stats["by_source"].get(source, 0) + 1
            
            # Create bulk record
            bulk_data = MetricBulkCreate(metrics=metrics_to_create)
            
            # Save to database
            db = SessionLocal()
            try:
                created_metrics = create_metrics_bulk(db, bulk_data.metrics)
                total_created += len(created_metrics)
                
                # Print progress
                print(f"[{timestamp}] Batch #{batch_count} ✅ {len(created_metrics)} metrics created | Total: {total_created}")
                
                # Detailed stats
                type_str = " | ".join([f"{t}:{''.join(chr(0x2588) for _ in range(c))}" for t, c in batch_stats["by_type"].items()])
                source_str = " | ".join([f"{s}:{c}" for s, c in batch_stats["by_source"].items()])
                print(f"  Types: {type_str}")
                print(f"  Sources: {source_str}\n")
                
            except Exception as e:
                print(f"[{timestamp}] Batch #{batch_count} ❌ ERROR: {str(e)}\n")
            finally:
                db.close()
            
            # Wait before next batch
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print(f"🛑 STOPPED BY USER")
        print("=" * 70)
        print(f"📊 Total batches: {batch_count}")
        print(f"📥 Total metrics created: {total_created}")
        print(f"⏱️  Runtime: ~{batch_count * interval} seconds")
        print(f"⚡ Average: {total_created // max(batch_count, 1)} metrics per batch")
        print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate fake IoT sensor data (once or continuously)")
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="Number of metrics to generate per batch (default: 200 for once, 50 for continuous)"
    )
    parser.add_argument(
        "--spread-hours",
        type=int,
        default=None,
        help="Spread data over N hours (optional, only for one-time generation)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode (infinite loop)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=2,
        help="Interval in seconds between batches for continuous mode (default: 2)"
    )
    
    args = parser.parse_args()
    
    if args.continuous:
        # Continuous mode
        count_per_batch = args.count if args.count != 200 else 50  # Use custom count or default to 50
        generate_iot_data_continuous(count_per_batch=count_per_batch, interval=args.interval)
    elif args.spread_hours:
        # Time-spread mode
        result = generate_iot_data_spread_time(count=args.count, hours=args.spread_hours)
        sys.exit(0 if result.get("success", False) else 1)
    else:
        # One-time generation
        result = generate_iot_data(count=args.count)
        sys.exit(0 if result.get("success", False) else 1)
