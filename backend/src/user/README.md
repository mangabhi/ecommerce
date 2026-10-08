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

All endpoints require an access token in the `Authorization: Bearer <access_token>` header.

## Profile

`GET /api/v1/users/me` returns the authenticated user's account fields together with
their optional profile fields. `PATCH /api/v1/users/me` accepts any non-empty
combination of the following fields:

```json
{
  "full_name": "Alex Example",
  "phone": "+1-555-0100",
  "date_of_birth": "1990-01-15",
  "avatar_url": "https://example.com/avatar.png"
}
```

The account's email and role are read-only. `phone`, `date_of_birth`, and
`avatar_url` can be set to `null`.

## Addresses

`POST /api/v1/users/me/addresses` requires `recipient_name`, `address_line1`,
`city`, `state`, `postal_code`, and `country`. `label` defaults to `home`;
`phone`, `address_line2`, and `is_default` are optional.

```json
{
  "label": "home",
  "recipient_name": "Alex Example",
  "phone": "+1-555-0100",
  "address_line1": "123 Main Street",
  "address_line2": "Apt 4",
  "city": "Springfield",
  "state": "IL",
  "postal_code": "62701",
  "country": "US",
  "is_default": true
}
```

`PATCH /api/v1/users/me/addresses/{id}` accepts any non-empty subset of address
fields. Setting an address as the default clears the default flag from the user's
other addresses. Address lookups are scoped to the authenticated user; an address
owned by another user returns `404`.
