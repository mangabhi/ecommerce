
from src.products.models import Product


def compare_products(products: list[Product]) -> str:
    """Generate a structured comparison summary."""

    if len(products) < 2:
        return "At least two products are required for comparison."

    cheapest = min(products, key=lambda product: product.price)
    most_expensive = max(products, key=lambda product: product.price)

    price_difference = most_expensive.price - cheapest.price

    comparison = [
        f"Compared {len(products)} products.",
        (
            f"The lowest-priced option is {cheapest.name} "
            f"at ${cheapest.price}."
        ),
        (
            f"The price difference between the cheapest and "
            f"most expensive products is ${price_difference}."
        ),
    ]

    for product in products:
        category = product.category.name if product.category else "Uncategorized"

        comparison.append(
            f"{product.name}: ${product.price}, "
            f"Category: {category}. "
            f"Description: {product.description or 'Not available'}."
        )

    return " ".join(comparison)
