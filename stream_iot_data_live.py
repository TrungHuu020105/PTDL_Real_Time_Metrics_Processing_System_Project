"""
Live IoT Data Streamer - Send sensor data directly to Dashboard via WebSocket
(No database save - pure real-time streaming)

Usage:
    python stream_iot_data_live.py                      # Stream to localhost
    python stream_iot_data_live.py --server 192.168.1.100:8000
    python stream_iot_data_live.py --interval 10        # Custom interval
"""

import asyncio
import json
import argparse
from datetime import datetime
import sys

try:
    import websockets
    # Don't import deprecated class
except ImportError:
    print("❌ websockets not installed. Install with:")
    print("   pip install websockets")
    sys.exit(1)

# Import sensor generation logic
from generate_iot_data import IoTDataGenerator


class LiveIoTStreamer:
    """Stream live sensor data to dashboard without database save"""
    
    def __init__(self, server_url: str = "ws://localhost:8000/api/ws/iot_generator", interval: int = 5):
        self.server_url = server_url
        self.interval = interval
        self.generator = IoTDataGenerator()
        self.batch_count = 0
        self.total_records = 0
        self.ws = None  # WebSocket connection
    
    async def connect(self):
        """Connect to WebSocket"""
        try:
            print(f"🔗 Connecting to {self.server_url}...")
            self.ws = await websockets.connect(self.server_url)
            print(f"✅ Connected! Ready to stream data.\n")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    async def stream_batch(self):
        """Generate 1 batch and stream to dashboard"""
        self.batch_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Generate 1 batch (5 metrics)
            metrics_to_send = self.generator.run_once(save_to_db=False)
            
            if not metrics_to_send:
                return
            
            total_generated = len(metrics_to_send["metrics"])
            total_saved = len([m for m in metrics_to_send["metrics"] if m.get("saved", True)])
            total_dropped = total_generated - total_saved
            
            self.total_records += total_generated
            
            # Send EACH metric to WebSocket (ALL data, no filtering)
            # Frontend will receive 100% of data for smooth realtime display
            for metric in metrics_to_send["metrics"]:
                data = {
                    "timestamp": metric.get("timestamp", datetime.now().isoformat()),
                    "metric_type": metric.get("metric_type"),
                    "value": metric.get("value"),
                    "source": metric.get("source"),
                    "unit": metric.get("unit", ""),
                    "saved": metric.get("saved", False)  # Flag for backend DB filtering
                }
                
                # Send to WebSocket
                if self.ws is not None:
                    await self.ws.send(json.dumps(data))
            
            # Print batch summary
            print(f"[{timestamp}] Batch #{self.batch_count} | "
                  f"Generated: {total_generated} | "
                  f"DB-Worthy: {total_saved} | "
                  f"Realtime-Only: {total_dropped}")
            
            # Print detail per sensor
            for metric in metrics_to_send["metrics"]:
                status = "📊 STREAM" if metric.get("saved", True) else "📡 STREAM*"
                reason = metric.get("reason", "sent to dashboard")
                print(f"  {status} {metric['metric_type']:20} = {metric['value']:8.2f} {metric['unit']:5} | {reason}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error in batch: {e}")
            raise
    
    async def run_continuous(self):
        """Stream data continuously"""
        print("=" * 100)
        print("🚀 LIVE IoT DATA STREAMER (Real-Time Dashboard Feed)")
        print("=" * 100)
        print(f"📡 Server: {self.server_url}")
        print(f"⏰ Interval: {self.interval}s per batch")
        print(f"📊 Each batch: 5 metrics (temperature, humidity, etc.)")
        print("🛑 Press Ctrl+C to stop\n")
        
        try:
            while True:
                try:
                    if self.ws is None:
                        await self.connect()
                    
                    await self.stream_batch()
                    await asyncio.sleep(self.interval)
                
                except Exception as e:
                    print(f"❌ Connection error: {e}")
                    print("🔄 Attempting to reconnect in 3 seconds...")
                    self.ws = None
                    await asyncio.sleep(3)
        
        except KeyboardInterrupt:
            print("\n" + "=" * 100)
            print("🛑 STOPPED BY USER")
            print("=" * 100)
            print(f"📊 Total batches streamed: {self.batch_count}")
            print(f"📥 Total metrics sent: {self.total_records}")
            print(f"⏱️  Runtime: ~{self.batch_count * self.interval} seconds")
            print(f"⚡ Average: {self.total_records // max(self.batch_count, 1)} metrics per batch")
            print("=" * 100)
        
        finally:
            if self.ws:
                await self.ws.close()
                print("🔌 Disconnected from WebSocket\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Stream live IoT sensor data to dashboard (no database save)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stream_iot_data_live.py                              # Stream to localhost:8000
  python stream_iot_data_live.py --server 192.168.1.100:8000 # Custom server
  python stream_iot_data_live.py --interval 10                # 10s between batches
        """
    )
    parser.add_argument(
        "--server",
        type=str,
        default="localhost:8000",
        help="WebSocket server (default: localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval in seconds (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Build WebSocket URL
    server_url = f"ws://{args.server}/api/ws/iot_generator"
    
    # Run streamer
    streamer = LiveIoTStreamer(server_url=server_url, interval=args.interval)
    asyncio.run(streamer.run_continuous())


if __name__ == "__main__":
    main()
