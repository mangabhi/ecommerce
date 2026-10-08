from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.notifications.dtos import NotificationTestRequest
from src.notifications.models import Notification


def list_notifications(
    user_id: int,
    unread_only: bool,
    limit: int,
    offset: int,
    db: Session,
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def mark_read(notification_id: int, user_id: int, db: Session) -> Notification:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification


def create_test_notification(
    user_id: int,
    body: NotificationTestRequest,
    db: Session,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=body.title,
        message=body.message,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
