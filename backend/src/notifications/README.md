Base path: /api/v1/notifications
Method	Endpoint	Purpose
GET	/notifications	List user notifications
PATCH	/notifications/{id}/read	Mark as read
POST	/notifications/test	Optional development-only test endpoint

All notification endpoints require an access token and are scoped to the
current user. `GET /notifications` accepts `unread_only`, `limit` (default
`50`, maximum `200`), and `offset`. Users can only mark their own notifications
as read. The test endpoint creates a notification for the current user and is
available only when `APP_ENV=development`.