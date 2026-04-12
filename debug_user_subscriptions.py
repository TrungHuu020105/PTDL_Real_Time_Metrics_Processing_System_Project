from app.database import SessionLocal
from app.models import User, ServerSubscription

db = SessionLocal()
user = db.query(User).filter(User.username=='user').first()
if user:
    print(f'User: {user.username} (ID: {user.id})')
    subs = db.query(ServerSubscription).filter(ServerSubscription.user_id==user.id).all()
    print(f'Subscriptions count: {len(subs)}')
    for sub in subs:
        print(f'  - Server {sub.server_id}')
    
    # Now check accessible sources
    from app.crud import get_user_accessible_sources
    sources = get_user_accessible_sources(db, user.id)
    print(f'Accessible sources: {sources}')
    
    # Check if system_monitor is in there
    if 'system_monitor' in sources:
        print('✓ system_monitor IS accessible')
    else:
        print('✗ system_monitor IS NOT accessible')
else:
    print('User not found')
db.close()
