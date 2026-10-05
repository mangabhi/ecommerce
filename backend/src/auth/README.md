# Authentication API

Base path: `/api/v1/auth`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Register a customer |
| POST | `/auth/login` | Log in |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Log out / revoke session |
| POST | `/auth/forgot-password` | Request password reset |   TBD
| POST | `/auth/reset-password` | Set a new password |  TBD

Learn: password hashing, JWT or secure session authentication, OAuth2 concepts, Pydantic validation, role-based access control, and secure token handling.
