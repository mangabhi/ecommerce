from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.notifications import controller
from src.notifications.dtos import NotificationResponse, NotificationTestRequest
from src.utils.db import get_db
from src.utils.helpers import is_authenticated
from src.utils.settings import settings

notification_routes = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@notification_routes.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.list_notifications(
        current_user.id,
        unread_only,
        limit,
        offset,
        db,
    )


@notification_routes.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.mark_read(notification_id, current_user.id, db)


@notification_routes.post(
    "/test",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_test_notification(
    body: NotificationTestRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return controller.create_test_notification(current_user.id, body, db)
