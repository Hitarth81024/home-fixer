from firebase_admin import messaging
from .models import FCMDevice


def send_push_notification(token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {},
    )
    response = messaging.send(message)
    return response


def notify_user(user, title, body, data=None):
    device = FCMDevice.objects.filter(user=user).first()
    if device:
        try:
            send_push_notification(
                token=device.token,
                title=title,
                body=body,
                data=data or {},
            )
        except Exception:
            pass
