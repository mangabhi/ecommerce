Base path: /api/v1/coupons
Method	Endpoint	Purpose
POST	/coupons/validate	Validate a coupon
POST	/admin/coupons	Create a coupon
PATCH	/admin/coupons/{id}	Update a coupon
GET	/admin/coupons	List coupons
POST	/checkout/quote	Calculate final checkout price

Coupon validation accepts `{"code": "SAVE10", "subtotal": 100.00}` and returns
the applicable discount and total. Coupons support `percentage` discounts
(1-100 percent) or fixed-amount discounts, an optional minimum subtotal,
maximum percentage discount, usage limit, start time, and expiry time.

Admin coupon management endpoints are `/api/v1/admin/coupons` and
`/api/v1/admin/coupons/{id}`. They require an admin access token. Create
requests require `code`, `discount_type`, and `discount_value`; codes are
case-insensitive and unique. `POST /api/v1/checkout/quote` requires the user's
access token and accepts an optional `{"code": "SAVE10"}` body; it calculates a
quote from the current cart without reserving the coupon or stock. Checkout
revalidates the coupon and records usage when creating the order. Usage is
released if payment fails or an unpaid order is cancelled.