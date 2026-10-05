# User API

Base path: `/api/v1/users`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/users/me` | Get current user's profile |
| PATCH | `/users/me` | Update profile |
| GET | `/users/me/addresses` | List saved addresses |
| POST | `/users/me/addresses` | Add an address |
| PATCH | `/users/me/addresses/{id}` | Update an address |
| DELETE | `/users/me/addresses/{id}` | Delete an address |
