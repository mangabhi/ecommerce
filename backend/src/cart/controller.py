from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.cart.models import Cart, CartItem
from src.products.models import Product


def _get_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _cart_payload(cart: Cart) -> dict:
    items = []
    subtotal = Decimal("0.00")
    for item in cart.items:
        line_total = Decimal(item.product.price) * item.quantity
        subtotal += line_total
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product": item.product,
                "subtotal": line_total,
            }
        )
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "items": items,
        "subtotal": subtotal,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
    }


def get_cart(user_id: int, db: Session) -> dict:
    return _cart_payload(_get_cart(user_id, db))


def add_item(user_id: int, product_id: int, quantity: int, db: Session) -> dict:
    cart = _get_cart(user_id, db)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )
    desired_quantity = quantity + item.quantity if item else quantity
    if desired_quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requested quantity exceeds available stock",
        )
    if item is None:
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity))
    else:
        item.quantity = desired_quantity
    db.commit()
    db.refresh(cart)
    return _cart_payload(cart)


def update_item(user_id: int, item_id: int, quantity: int, db: Session) -> dict:
    cart = _get_cart(user_id, db)
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requested quantity exceeds available stock",
        )
    item.quantity = quantity
    db.commit()
    db.refresh(cart)
    return _cart_payload(cart)


def remove_item(user_id: int, item_id: int, db: Session) -> dict:
    cart = _get_cart(user_id, db)
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return _cart_payload(cart)


def clear_cart(user_id: int, db: Session) -> None:
    cart = _get_cart(user_id, db)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
