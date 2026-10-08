# Categories API

Base path: `/api/v1/categories`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/categories` | List categories |
| GET | `/categories/{id}/products` | Products in a category |

Both endpoints are public. Categories are returned alphabetically by name;
products in a category are returned alphabetically by name and include active
products only. A category ID that does not exist returns `404`.

Products can be assigned to a category when they are created or updated by
setting `category_id`. The field is optional, and setting it to `null` on an
update removes the association. Categories are read-only through this API and
must already exist before they can be assigned to a product.
