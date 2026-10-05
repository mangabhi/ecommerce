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
