# Products API

Base path: `/api/v1/products`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/products` | List products |
| GET | `/products/{id}` | Product details |
| POST | `/products` | Create a product (admin) |
| PATCH | `/products/{id}` | Update a product (admin) |
| DELETE | `/products/{id}` | Archive/remove a product (admin) |
| GET | `/products?search=phone` | Search products |
| GET | `/products?min_price=500&max_price=2000` | Filter by price |
| GET | `/products?sort_by=price&order=asc` | Sort products |

Product listings and details are public and include active products only.
Archived products return `404` from the detail endpoint. Admin-only create,
update, and delete endpoints require an authenticated user whose role is
`admin`; provide a valid access token in the `Authorization` header.
Deleting a product archives it rather than permanently removing it.

## Product fields

Create requests require `name` and `price`. `price` is a non-negative decimal
with at most two fractional digits. `stock_quantity` defaults to `0` and must
be non-negative; `description` and `image_url` are optional and may be `null`.
`category_id` is optional and references an existing category.
For example:

```json
{
  "name": "Example phone",
  "category_id": 1,
  "description": "Unlocked smartphone",
  "price": 799.99,
  "stock_quantity": 12,
  "image_url": "https://example.com/phone.png"
}
```

Updates accept a non-empty subset of those fields; setting `category_id` to
`null` removes the product's category. The list endpoint supports
case-insensitive search over product names and descriptions, inclusive price
filters, and sorting by `name`, `price`, or `created_at` with `asc` or `desc`
order. Listings default to 20 products and support `limit` (1-100) and
`offset` pagination.
