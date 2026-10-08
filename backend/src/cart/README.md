Base path: /api/v1/cart
Method	Endpoint	Purpose
GET	/cart	Get current cart
POST	/cart/items	Add an item
PATCH	/cart/items/{item_id}	Change quantity
DELETE	/cart/items/{item_id}	Remove an item
DELETE	/cart	Clear cart

All cart endpoints require an access token. Each user has one cart. Add an item
with `{"product_id": 12, "quantity": 2}`; adding a product already in the cart
increases its quantity. Patch an item with `{"quantity": 3}`. Quantities must be
positive and cannot exceed available stock. The cart response includes its
items, current product details, line subtotals, and cart subtotal. Removing an
item returns the updated cart; clearing the cart returns `204 No Content`.