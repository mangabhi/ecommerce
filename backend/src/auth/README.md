# Authentication API

Base path: `/api/v1/auth`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Register a customer |
| POST | `/auth/login` | Log in |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke the refresh token |
| POST | `/auth/forgot-password` | Request password reset |   TBD
| POST | `/auth/reset-password` | Set a new password |  TBD

Learn: password hashing, JWT or secure session authentication, OAuth2 concepts, Pydantic validation, role-based access control, and secure token handling.

To log out, send `POST /api/v1/auth/logout` with the refresh token in the JSON body:

```json
{
  "refresh_token": "<refresh-token>"
}
```

The revoked refresh token can no longer be used to obtain access tokens. Existing access tokens remain valid until they expire.
