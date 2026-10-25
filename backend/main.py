from fastapi import FastAPI
from sqlalchemy import inspect, text
from src.utils.db import Base,engine
from src.auth.router import auth_routes
from src.user.router import admin_user_routes, user_routes
from src.user.models import Address, UserProfile
from src.products.router import product_routes
from src.products.models import Product
from src.categories.router import category_routes
from src.categories.models import Category
from src.cart.router import cart_routes
from src.cart.models import Cart, CartItem
from src.inventory.router import inventory_routes
from src.inventory.models import InventoryAdjustment
from src.orders.router import order_routes, checkout_routes, admin_order_routes
from src.orders.models import Order, OrderItem
from src.payment.router import payment_routes
from src.payment.models import Payment
from src.coupons.router import coupon_routes, checkout_quote_routes, admin_coupon_routes
from src.coupons.models import Coupon, CouponRedemption
from src.review_wishlist.router import review_wishlist_routes
from src.review_wishlist.models import Review, WishlistItem
from src.notifications.router import notification_routes
from src.notifications.models import Notification

Base.metadata.create_all(engine)


def ensure_payment_method_id_column(database_engine=engine):
    payment_columns = {
        column["name"] for column in inspect(database_engine).get_columns("payment")
    }
    if "payment_method_id" not in payment_columns:
        with database_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE payment ADD COLUMN payment_method_id VARCHAR(128)")
            )


ensure_payment_method_id_column()

app=FastAPI(title="Authentication User",description="This API will check if the user is valid or not")
@app.get("/health")
def health_check():
    return {"status":"healthy"}
app.include_router(auth_routes)
app.include_router(user_routes)
app.include_router(admin_user_routes)
app.include_router(product_routes)
app.include_router(category_routes)
app.include_router(cart_routes)
app.include_router(inventory_routes)
app.include_router(order_routes)
app.include_router(checkout_routes)
app.include_router(admin_order_routes)
app.include_router(coupon_routes)
app.include_router(admin_coupon_routes)
app.include_router(checkout_quote_routes)
app.include_router(payment_routes)
app.include_router(review_wishlist_routes)
app.include_router(notification_routes)


# @app.get('/')
# def firstFunc():
#     return "Here our server is running."
