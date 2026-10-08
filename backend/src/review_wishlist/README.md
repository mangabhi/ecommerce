Method	Endpoint	Purpose
GET	/products/{id}/reviews	List product reviews
POST	/products/{id}/reviews	Add a review
PATCH	/reviews/{id}	Edit your review
DELETE	/reviews/{id}	Delete your review
GET	/wishlist	Get saved products
POST	/wishlist/items	Add a product
DELETE	/wishlist/items/{product_id}	Remove a product

Listing product reviews is public. Adding, editing, or deleting reviews and all
wishlist endpoints require an access token. A user may leave one review per
product; ratings must be from 1 through 5. Reviews can only be edited or
deleted by their author. `POST /wishlist/items` accepts a JSON body such as
`{"product_id": 12}`; adding an existing wishlist item is idempotent.