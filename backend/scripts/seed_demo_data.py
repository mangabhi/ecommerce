import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.auth.controller import get_password_hash
from src.auth.models import AuthUser
from src.cart.models import Cart, CartItem
from src.categories.models import Category
from src.coupons.models import Coupon, CouponRedemption
from src.inventory.models import InventoryAdjustment
from src.notifications.models import Notification
from src.orders.models import Order, OrderItem
from src.payment.models import Payment
from src.products.models import Product
from src.review_wishlist.models import Review, WishlistItem
from src.user.models import Address, UserProfile
from src.utils.db import Base, LocalSession, engine


BACKEND_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIRS = (
    "auth",
    "user",
    "categories",
    "products",
    "cart",
    "inventory",
    "coupons",
    "orders",
    "payment",
    "review_wishlist",
    "notifications",
)


def _fixture(module: str) -> dict[str, Any]:
    fixture_path = BACKEND_DIR / "src" / module / "seed_data.json"
    with fixture_path.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _decimal(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def _get_or_create(
    db: Session,
    model: type,
    lookup: dict[str, Any],
    values: dict[str, Any],
) -> tuple[Any, bool]:
    instance = db.query(model).filter_by(**lookup).first()
    if instance is not None:
        return instance, False
    instance = model(**lookup, **values)
    db.add(instance)
    db.flush()
    return instance, True


def _required(mapping: dict[str, Any], key: str, description: str) -> Any:
    try:
        return mapping[key]
    except KeyError as error:
        raise ValueError(f"Missing {description}: {key}") from error


def seed_demo_data() -> dict[str, int]:
    if os.getenv("APP_ENV", "").strip().lower() != "development":
        raise RuntimeError(
            "Refusing to seed sample data unless APP_ENV=development. "
            "Set this only for a development/test database."
        )

    Base.metadata.create_all(bind=engine)
    counts = {module: 0 for module in FIXTURE_DIRS}

    with LocalSession() as db, db.begin():
        users: dict[str, AuthUser] = {}
        for row in _fixture("auth")["users"]:
            user, created = _get_or_create(
                db,
                AuthUser,
                {"email": row["email"]},
                {
                    "password_hash": get_password_hash(row["password"]),
                    "full_name": row["full_name"],
                    "phone": row["phone"],
                    "role": row["role"],
                    "is_active": True,
                    "is_verified": row["is_verified"],
                },
            )
            users[user.email] = user
            counts["auth"] += int(created)

        for row in _fixture("user")["profiles"]:
            user = _required(users, row["email"], "profile user")
            _, created = _get_or_create(
                db,
                UserProfile,
                {"user_id": user.id},
                {
                    "date_of_birth": date.fromisoformat(row["date_of_birth"]),
                    "avatar_url": row["avatar_url"],
                },
            )
            counts["user"] += int(created)

        addresses: dict[tuple[str, str], Address] = {}
        for row in _fixture("user")["addresses"]:
            user = _required(users, row["email"], "address user")
            address, created = _get_or_create(
                db,
                Address,
                {
                    "user_id": user.id,
                    "label": row["label"],
                    "address_line1": row["address_line1"],
                },
                {
                    key: value
                    for key, value in row.items()
                    if key not in {"email", "label", "address_line1"}
                },
            )
            addresses[(user.email, row["label"])] = address
            counts["user"] += int(created)

        categories: dict[str, Category] = {}
        for row in _fixture("categories")["categories"]:
            category, created = _get_or_create(
                db,
                Category,
                {"name": row["name"]},
                {"description": row["description"]},
            )
            categories[category.name] = category
            counts["categories"] += int(created)

        products: dict[str, Product] = {}
        for row in _fixture("products")["products"]:
            category_name = row["category"]
            category = _required(categories, category_name, "product category")
            product, created = _get_or_create(
                db,
                Product,
                {"name": row["name"]},
                {
                    "category_id": category.id,
                    "description": row["description"],
                    "price": _decimal(row["price"]),
                    "stock_quantity": row["stock_quantity"],
                    "image_url": row["image_url"],
                    "is_active": True,
                },
            )
            products[product.name] = product
            counts["products"] += int(created)

        for row in _fixture("cart")["carts"]:
            user = _required(users, row["email"], "cart user")
            cart, created = _get_or_create(db, Cart, {"user_id": user.id}, {})
            counts["cart"] += int(created)
            for cart_row in row["items"]:
                product = _required(products, cart_row["product"], "cart product")
                _, created = _get_or_create(
                    db,
                    CartItem,
                    {"cart_id": cart.id, "product_id": product.id},
                    {"quantity": cart_row["quantity"]},
                )
                counts["cart"] += int(created)

        coupons: dict[str, Coupon] = {}
        for row in _fixture("coupons")["coupons"]:
            values = {
                **row,
                "discount_value": _decimal(row["discount_value"]),
                "minimum_order_amount": _decimal(row["minimum_order_amount"]),
                "maximum_discount": (
                    _decimal(row["maximum_discount"])
                    if row["maximum_discount"] is not None
                    else None
                ),
            }
            coupon, created = _get_or_create(
                db,
                Coupon,
                {"code": row["code"]},
                {
                    key: value
                    for key, value in values.items()
                    if key != "code"
                },
            )
            coupons[coupon.code] = coupon
            counts["coupons"] += int(created)

        orders: dict[str, Order] = {}
        order_fixtures = _fixture("orders")["orders"]
        for row in order_fixtures:
            user = _required(users, row["email"], "order user")
            lookup: dict[str, Any] = (
                {"tracking_number": row["tracking_number"]}
                if row["tracking_number"]
                else {
                    "user_id": user.id,
                    "tracking_status": row["tracking_status"],
                }
            )
            order = db.query(Order).filter_by(**lookup).first()
            created = order is None
            if order is None:
                address = _required(
                    addresses,
                    (user.email, row["address_label"]),
                    "order shipping address",
                )
                shipping_address = {
                    "label": address.label,
                    "recipient_name": address.recipient_name,
                    "phone": address.phone,
                    "address_line1": address.address_line1,
                    "address_line2": address.address_line2,
                    "city": address.city,
                    "state": address.state,
                    "postal_code": address.postal_code,
                    "country": address.country,
                }
                order = Order(
                    user_id=user.id,
                    status=row["status"],
                    subtotal=_decimal(row["subtotal"]),
                    discount_amount=_decimal(row["discount_amount"]),
                    total=_decimal(row["total"]),
                    coupon_code=row["coupon_code"],
                    shipping_address=shipping_address,
                    tracking_number=row["tracking_number"],
                    tracking_status=row["tracking_status"],
                )
                db.add(order)
                db.flush()
            orders[row["key"]] = order
            counts["orders"] += int(created)

            for item_row in row["items"]:
                product = _required(products, item_row["product"], "order product")
                _, created = _get_or_create(
                    db,
                    OrderItem,
                    {"order_id": order.id, "product_id": product.id},
                    {
                        "product_name": product.name,
                        "unit_price": _decimal(item_row["unit_price"]),
                        "quantity": item_row["quantity"],
                    },
                )
                counts["orders"] += int(created)

        for row in _fixture("inventory")["adjustments"]:
            product = _required(products, row["product"], "inventory product")
            _, created = _get_or_create(
                db,
                InventoryAdjustment,
                {
                    "product_id": product.id,
                    "reason": row["reason"],
                },
                {
                    "adjusted_by": _required(
                        users,
                        "demo.admin@example.com",
                        "inventory admin",
                    ).id,
                    "change": row["change"],
                    "stock_after": product.stock_quantity,
                },
            )
            counts["inventory"] += int(created)

        for row in _fixture("payment")["payments"]:
            order = _required(orders, row["order_key"], "payment order")
            payment, created = _get_or_create(
                db,
                Payment,
                {"provider_reference": row["provider_reference"]},
                {
                    "order_id": order.id,
                    "user_id": order.user_id,
                    "provider": row["provider"],
                    "status": row["status"],
                    "amount": _decimal(row["amount"]),
                    "currency": row["currency"],
                },
            )
            counts["payment"] += int(created)

        for row in _fixture("coupons")["coupons"]:
            coupon = _required(coupons, row["code"], "redemption coupon")
            if row["code"] != "WELCOME10":
                continue
            order = _required(orders, "demo-shipped-order", "coupon redemption order")
            _, created = _get_or_create(
                db,
                CouponRedemption,
                {
                    "coupon_id": coupon.id,
                    "user_id": order.user_id,
                    "order_id": order.id,
                },
                {},
            )
            counts["coupons"] += int(created)

        for row in _fixture("review_wishlist")["reviews"]:
            user = _required(users, row["email"], "review user")
            product = _required(products, row["product"], "review product")
            _, created = _get_or_create(
                db,
                Review,
                {"product_id": product.id, "user_id": user.id},
                {
                    "rating": row["rating"],
                    "title": row["title"],
                    "body": row["body"],
                },
            )
            counts["review_wishlist"] += int(created)

        for row in _fixture("review_wishlist")["wishlist"]:
            user = _required(users, row["email"], "wishlist user")
            product = _required(products, row["product"], "wishlist product")
            _, created = _get_or_create(
                db,
                WishlistItem,
                {"user_id": user.id, "product_id": product.id},
                {},
            )
            counts["review_wishlist"] += int(created)

        for row in _fixture("notifications")["notifications"]:
            user = _required(users, row["email"], "notification user")
            values = {
                "is_read": row["is_read"],
                "read_at": datetime.now(timezone.utc) if row["is_read"] else None,
            }
            _, created = _get_or_create(
                db,
                Notification,
                {
                    "user_id": user.id,
                    "title": row["title"],
                    "message": row["message"],
                },
                values,
            )
            counts["notifications"] += int(created)

    return counts


if __name__ == "__main__":
    inserted = seed_demo_data()
    print(f"Demo data seeded into {engine.dialect.name}. Newly inserted records:")
    for service, count in inserted.items():
        print(f"  {service}: {count}")
    print("Demo customer/admin login: demo.customer@example.com / demo.admin@example.com")
    print("Shared demo password: DemoPass123!")
