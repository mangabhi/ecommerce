Base path: /api/v1/orders and /api/v1/checkout
Method	Endpoint	Purpose
POST	/checkout	Validate cart and initiate checkout
POST	/orders	Create an order
GET	/orders	List the customer's orders
GET	/orders/{order_id}	Order details
POST	/orders/{order_id}/cancel	Request cancellation
GET	/orders/{order_id}/tracking	Get shipping status
GET	/admin/orders	List all orders (admin)
PATCH	/admin/orders/{order_id}/status	Update order status (admin)

All customer order and checkout endpoints require an access token and operate
only on that user's orders. Both `POST /checkout` and `POST /orders` create an
order from the current cart; the JSON body requires the user's saved
`address_id` and may include a `coupon_code`:

```json
{"address_id": 4, "coupon_code": "SAVE10"}
```

Checkout verifies current product stock, reserves it, stores a shipping
address snapshot, applies the optional coupon, creates a `pending_payment`
order, and clears the cart. Start payment through the payments API. Cancellation
of an unpaid order is immediate; cancellation of a paid or processing order is
recorded as `cancellation_requested` for admin handling. Tracking returns the
order status and any assigned tracking number/status.

The admin endpoints are `/api/v1/admin/orders` and
`/api/v1/admin/orders/{order_id}/status`. Admin status updates may transition
paid orders to processing or cancelled, processing orders to shipped or
cancelled, shipped orders to delivered, and cancellation requests to cancelled
or back to processing. Shipping requires a `tracking_number`.