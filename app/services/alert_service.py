"""Alert notification dispatcher."""

import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.models import Alert, IoTDevice, User, UserNotificationTarget
from app.services.email_service import send_email_alert
from app.services.telegram_service import send_telegram_message


def _build_telegram_message(alert: Alert, device: IoTDevice) -> str:
    status_text = "QUÁ CAO" if alert.status == "critical" else "QUÁ THẤP"
    return (
        "🔺 ⚠️ CẢNH BÁO THIẾT BỊ ⚠️\n\n"
        f"📱 Thiết bị: {device.name}\n"
        f"📊 Loại: {alert.metric_type}\n"
        f"location: {device.location or 'N/A'}\n"
        f"Trạng thái: {status_text}\n\n"
        f"📈 Giá trị hiện tại: {alert.current_value}\n"
        f"⚠️ Ngưỡng: {alert.threshold}\n\n"
        f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


def _build_email_html(alert: Alert, device: IoTDevice) -> str:
    status_text = "QUÁ CAO" if alert.status == "critical" else "QUÁ THẤP"
    return f"""
    <html>
      <body>
        <h2>🔺 ⚠️ CẢNH BÁO THIẾT BỊ ⚠️</h2>
        <p><b>📱 Thiết bị:</b> {device.name}</p>
        <p><b>📊 Loại:</b> {alert.metric_type}</p>
        <p><b>location:</b> {device.location or 'N/A'}</p>
        <p><b>Trạng thái:</b> {status_text}</p>
        <p><b>📈 Giá trị hiện tại:</b> {alert.current_value}</p>
        <p><b>⚠️ Ngưỡng:</b> {alert.threshold}</p>
        <p><b>⏰ Thời gian:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
      </body>
    </html>
    """


async def dispatch_alert_notifications(alert_id: int):
    """Dispatch Telegram and email notifications asynchronously for device owner."""
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            print(f"[NOTIFY] Alert {alert_id} not found")
            return
        device = db.query(IoTDevice).filter(IoTDevice.source == alert.source).first()
        if not device:
            print(f"[NOTIFY] No device found for source={alert.source}")
            return
        owner = db.query(User).filter(User.id == device.user_id).first()
        if not owner:
            print(f"[NOTIFY] No owner found for device_id={device.id}")
            return

        tasks = []
        targets = db.query(UserNotificationTarget).filter(
            UserNotificationTarget.user_id == owner.id,
            UserNotificationTarget.is_enabled == True
        ).all()

        telegram_targets = [t.target_value for t in targets if t.target_type == "telegram"]
        email_targets = [t.target_value for t in targets if t.target_type == "email"]

        for chat_id in telegram_targets:
            telegram_message = _build_telegram_message(alert, device)
            tasks.append(asyncio.to_thread(send_telegram_message, chat_id, telegram_message))

        for email in email_targets:
            html = _build_email_html(alert, device)
            subject = f"[IoT Alert] {alert.metric_type} on {device.name}"
            tasks.append(asyncio.to_thread(send_email_alert, email, subject, html))

        # Backward compatibility for old single-target fields
        if not telegram_targets and owner.telegram_enabled and owner.telegram_chat_id:
            telegram_message = _build_telegram_message(alert, device)
            tasks.append(asyncio.to_thread(send_telegram_message, owner.telegram_chat_id, telegram_message))
        if not email_targets:
            destination_email = owner.notification_email or owner.email
            if owner.email_enabled and destination_email:
                html = _build_email_html(alert, device)
                subject = f"[IoT Alert] {alert.metric_type} on {device.name}"
                tasks.append(asyncio.to_thread(send_email_alert, destination_email, subject, html))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            print(f"[NOTIFY] Dispatch results for alert_id={alert_id}: {results}")
        else:
            print(f"[NOTIFY] No channels enabled for user_id={owner.id}")
    finally:
        db.close()
