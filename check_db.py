from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Device, UserDevicePermission, User

engine = create_engine("sqlite:///metrics.db")
db = Session(engine)

devices = db.query(Device).all()
print(f"Total devices: {len(devices)}")
for d in devices:
    print(f"  - {d.name} (source: {d.source}, id: {d.id})")

print("\nAdmin permissions:")
admin = db.query(User).filter(User.username == "admin").first()
if admin:
    perms = db.query(UserDevicePermission).filter(UserDevicePermission.user_id == admin.id).all()
    print(f"  Admin has {len(perms)} permissions")
    for p in perms:
        print(f"    - Device {p.device_id}")

db.close()
