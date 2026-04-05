from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Device, UserDevicePermission

engine = create_engine("sqlite:///metrics.db")
db = Session(engine)

# Delete old devices by source
old_sources = ["server_1", "sensor_temp_1", "sensor_humidity_1"]

for source in old_sources:
    device = db.query(Device).filter(Device.source == source).first()
    if device:
        # Delete permissions first
        db.query(UserDevicePermission).filter(UserDevicePermission.device_id == device.id).delete()
        # Delete device
        db.delete(device)
        db.commit()
        print(f"✓ Deleted: {device.name} (source: {source})")

print("\nRemaining devices:")
devices = db.query(Device).all()
for d in devices:
    print(f"  - {d.name} (source: {d.source})")

db.close()
