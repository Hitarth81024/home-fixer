from firebase_admin import messaging

def send_push_notification(token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {},
    )
    response = messaging.send(message)
    return response
