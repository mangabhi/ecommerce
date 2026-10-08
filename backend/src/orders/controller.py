from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from src.cart.models import Cart, CartItem
from src.coupons.controller import validate_coupon
from src.coupons.models import Coupon, CouponRedemption
from src.notifications.models import Notification
from src.orders.dtos import OrderCreateRequest, OrderStatusUpdateRequest
from src.orders.models import Order, OrderItem
from src.payment.models import Payment
from src.products.models import Product
from src.user.models import Address


def _get_order(order_id: int, user_id: int, db: Session) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def create_order(user_id: int, body: OrderCreateRequest, db: Session) -> Order:
    address = (
        db.query(Address)
        .filter(Address.id == body.address_id, Address.user_id == user_id)
        .first()
    )
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping address not found")
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if cart is None or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    subtotal = sum(
        (Decimal(item.product.price) * item.quantity for item in cart.items),
        start=Decimal("0.00"),
    )
    coupon = None
    discount = Decimal("0.00")
    if body.coupon_code:
        coupon, discount = validate_coupon(body.coupon_code, subtotal, db)

    order = Order(
        user_id=user_id,
        status="pending_payment",
        subtotal=subtotal,
        discount_amount=discount,
        total=subtotal - discount,
        coupon_code=coupon.code if coupon else None,
        shipping_address={
            "recipient_name": address.recipient_name,
            "phone": address.phone,
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "city": address.city,
            "state": address.state,
            "postal_code": address.postal_code,
            "country": address.country,
        },
    )
    db.add(order)
    try:
        db.flush()
        for cart_item in cart.items:
            product = cart_item.product
            result = db.execute(
                update(Product)
                .where(
                    Product.id == product.id,
                    Product.is_active.is_(True),
                    Product.stock_quantity >= cart_item.quantity,
                )
                .values(stock_quantity=Product.stock_quantity - cart_item.quantity)
            )
            if result.rowcount != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for {product.name}",
                )
            order.items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=cart_item.quantity,
                )
            )
        if coupon is not None:
            coupon_update = update(Coupon).where(Coupon.id == coupon.id)
            if coupon.usage_limit is not None:
                coupon_update = coupon_update.where(Coupon.usage_count < coupon.usage_limit)
            result = db.execute(
                coupon_update.values(usage_count=Coupon.usage_count + 1)
            )
            if result.rowcount != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Coupon usage limit reached",
                )
            db.add(
                CouponRedemption(
                    coupon_id=coupon.id,
                    user_id=user_id,
                    order_id=order.id,
                )
            )
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.add(
            Notification(
                user_id=user_id,
                title="Order placed",
                message=f"Order #{order.id} was created and is awaiting payment.",
            )
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    db.refresh(order)
    return _get_order(order.id, user_id, db)


def list_orders(user_id: int, db: Session) -> list[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .all()
    )


def get_order(order_id: int, user_id: int, db: Session) -> Order:
    return _get_order(order_id, user_id, db)


def request_cancellation(
    order_id: int,
    user_id: int,
    reason: str | None,
    db: Session,
) -> Order:
    order = _get_order(order_id, user_id, db)
    if order.status == "pending_payment":
        order.status = "cancelled"
        _restore_stock(order, db)
        _release_coupon(order, db)
        db.query(Payment).filter(
            Payment.order_id == order.id,
            Payment.status == "pending",
        ).update(
            {"status": "cancelled"},
            synchronize_session=False,
        )
    elif order.status in {"paid", "processing"}:
        order.status = "cancellation_requested"
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order cannot be cancelled while it is {order.status}",
        )
    order.cancellation_reason = reason
    db.add(
        Notification(
            user_id=user_id,
            title="Cancellation requested",
            message=f"Cancellation requested for order #{order.id}.",
        )
    )
    db.commit()
    return _get_order(order.id, user_id, db)


def get_tracking(order_id: int, user_id: int, db: Session) -> dict:
    order = _get_order(order_id, user_id, db)
    return {
        "order_id": order.id,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "tracking_status": order.tracking_status,
        "updated_at": order.updated_at,
    }


def list_all_orders(limit: int, offset: int, db: Session) -> list[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_order_status(
    order_id: int,
    body: OrderStatusUpdateRequest,
    db: Session,
) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status in {"cancelled", "delivered", "refunded"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order cannot be changed from {order.status}",
        )
    allowed_transitions = {
        "paid": {"processing", "cancelled"},
        "processing": {"shipped", "cancelled"},
        "shipped": {"delivered"},
        "cancellation_requested": {"cancelled", "processing"},
    }
    if body.status not in allowed_transitions.get(order.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order cannot transition from {order.status} to {body.status}",
        )
    if body.status == "cancelled":
        _restore_stock(order, db)
    if body.status in {"shipped", "delivered"} and not order.tracking_number:
        tracking_number = body.tracking_number
        if not tracking_number:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tracking_number is required when shipping an order",
            )
        order.tracking_number = tracking_number
    order.status = body.status
    if body.tracking_number is not None:
        order.tracking_number = body.tracking_number
    if body.tracking_status is not None:
        order.tracking_status = body.tracking_status
    db.add(
        Notification(
            user_id=order.user_id,
            title="Order status updated",
            message=f"Order #{order.id} is now {order.status}.",
        )
    )
    db.commit()
    return _get_order(order.id, order.user_id, db)


def _restore_stock(order: Order, db: Session) -> None:
    for item in order.items:
        if item.product_id is not None:
            db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(stock_quantity=Product.stock_quantity + item.quantity)
            )


def _release_coupon(order: Order, db: Session) -> None:
    if order.coupon_code is None:
        return
    coupon = db.query(Coupon).filter(Coupon.code == order.coupon_code).first()
    if coupon is None:
        return
    result = db.execute(
        update(Coupon)
        .where(Coupon.id == coupon.id, Coupon.usage_count > 0)
        .values(usage_count=Coupon.usage_count - 1)
    )
    if result.rowcount == 1:
        db.query(CouponRedemption).filter(
            CouponRedemption.order_id == order.id
        ).delete()
