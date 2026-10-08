Base path: /api/v1/inventory
Method	Endpoint	Purpose
GET	/inventory/{product_id}	Check available stock
PATCH	/inventory/{product_id}	Adjust stock (admin)
GET	/inventory/low-stock	Find low-stock products (admin)

The stock check is public. Stock adjustments and low-stock queries require an
admin access token. Adjust stock with a signed delta, for example
`{"change": 8, "reason": "Restock"}`; negative changes reduce stock and cannot
make it negative. `GET /inventory/low-stock` accepts `threshold` (default `10`)
and `limit` (default `100`, maximum `500`). Each adjustment is stored with its
delta, resulting stock level, admin, and optional reason.