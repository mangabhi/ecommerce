import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DB_CONNECTION"] = "sqlite://"

from main import app, ensure_payment_method_id_column
from src.auth.controller import create_token
from src.auth.models import AuthUser
from src.orders.models import Order
from src.payment.models import Payment
from src.user.models import UserProfile
from src.utils.db import Base, get_db
from src.utils.settings import settings


def test_payment_method_migration_adds_column_to_existing_database():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE payment (id INTEGER PRIMARY KEY)"))

    ensure_payment_method_id_column(engine)

    assert "payment_method_id" in {
        column["name"] for column in inspect(engine).get_columns("payment")
    }
    engine.dispose()


@pytest.fixture
def client_and_sessions():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine)

    def override_get_db():
        db = test_sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, test_sessions
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_user(test_sessions, role: str, email: str) -> tuple[int, dict[str, str]]:
    with test_sessions() as db:
        user = AuthUser(
            email=email,
            password_hash="unused-test-hash",
            full_name="Test User",
            role=role,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(user.id, "access", 15)
        return user.id, {"Authorization": f"Bearer {token}"}


def test_admin_user_management_requires_admin(client_and_sessions):
    client, test_sessions = client_and_sessions
    _, headers = create_user(test_sessions, "customer", "customer@example.com")

    response = client.get("/api/v1/admin/users", headers=headers)

    assert response.status_code == 403


def test_admin_can_list_and_update_user_roles(client_and_sessions):
    client, test_sessions = client_and_sessions
    admin_id, admin_headers = create_user(test_sessions, "admin", "admin@example.com")
    customer_id, _ = create_user(test_sessions, "customer", "customer@example.com")

    response = client.get(
        "/api/v1/admin/users",
        params={"search": "customer@example.com"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    listed_user = response.json()[0]
    assert {
        key: listed_user[key]
        for key in (
            "id",
            "email",
            "full_name",
            "role",
            "phone",
            "is_active",
            "is_verified",
        )
    } == {
        "id": customer_id,
        "email": "customer@example.com",
        "full_name": "Test User",
        "role": "customer",
        "phone": None,
        "is_active": True,
        "is_verified": True,
    }
    assert isinstance(listed_user["created_at"], str)
    assert "password_hash" not in listed_user

    response = client.patch(
        f"/api/v1/admin/users/{customer_id}",
        json={"role": "business", "full_name": "Business User"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "business"
    assert response.json()["full_name"] == "Business User"

    response = client.patch(
        f"/api/v1/admin/users/{admin_id}",
        json={"role": "customer"},
        headers=admin_headers,
    )

    assert response.status_code == 409


def test_admin_can_permanently_delete_customer_only(client_and_sessions):
    client, test_sessions = client_and_sessions
    _, admin_headers = create_user(test_sessions, "admin", "admin@example.com")
    customer_id, customer_headers = create_user(
        test_sessions,
        "customer",
        "customer@example.com",
    )
    business_id, _ = create_user(test_sessions, "business", "business@example.com")
    with test_sessions() as db:
        db.add(UserProfile(user_id=customer_id))
        db.commit()

    response = client.delete(
        f"/api/v1/admin/users/{business_id}",
        headers=admin_headers,
    )

    assert response.status_code == 409

    response = client.delete(
        f"/api/v1/admin/users/{customer_id}",
        headers=admin_headers,
    )

    assert response.status_code == 204
    with test_sessions() as db:
        assert db.query(AuthUser).filter(AuthUser.id == customer_id).first() is None
        assert db.query(UserProfile).filter(UserProfile.user_id == customer_id).first() is None
    assert client.get("/api/v1/users/me", headers=customer_headers).status_code == 401


def test_confirming_successful_stripe_payment_marks_order_paid(
    client_and_sessions,
    monkeypatch,
):
    client, test_sessions = client_and_sessions
    customer_id, headers = create_user(test_sessions, "customer", "buyer@example.com")
    with test_sessions() as db:
        order = Order(
            user_id=customer_id,
            status="pending_payment",
            subtotal=25,
            discount_amount=0,
            total=25,
            shipping_address={"recipient_name": "Test User"},
        )
        db.add(order)
        db.flush()
        payment = Payment(
            order_id=order.id,
            user_id=customer_id,
            provider="stripe",
            provider_reference="pi_test_success",
            status="pending",
            amount=25,
            currency="USD",
        )
        db.add(payment)
        db.commit()
        payment_id = payment.id
        order_id = order.id

    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_example")
    monkeypatch.setattr(
        "src.payment.controller.stripe.PaymentIntent.retrieve",
        Mock(
            return_value=SimpleNamespace(
                id="pi_test_success",
                status="succeeded",
                amount_received=2500,
                currency="usd",
                payment_method="pm_test_method",
            )
        ),
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/confirm",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["payment_method_id"] == "pm_test_method"
    with test_sessions() as db:
        assert db.query(Order).filter(Order.id == order_id).one().status == "paid"
        assert (
            db.query(Payment).filter(Payment.id == payment_id).one().payment_method_id
            == "pm_test_method"
        )


def test_confirming_processing_stripe_payment_keeps_order_pending(
    client_and_sessions,
    monkeypatch,
):
    client, test_sessions = client_and_sessions
    customer_id, headers = create_user(test_sessions, "customer", "buyer@example.com")
    with test_sessions() as db:
        order = Order(
            user_id=customer_id,
            status="pending_payment",
            subtotal=25,
            discount_amount=0,
            total=25,
            shipping_address={"recipient_name": "Test User"},
        )
        db.add(order)
        db.flush()
        payment = Payment(
            order_id=order.id,
            user_id=customer_id,
            provider="stripe",
            provider_reference="pi_test_processing",
            status="pending",
            amount=25,
            currency="USD",
        )
        db.add(payment)
        db.commit()
        payment_id = payment.id
        order_id = order.id

    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_example")
    monkeypatch.setattr(
        "src.payment.controller.stripe.PaymentIntent.retrieve",
        Mock(
            return_value=SimpleNamespace(
                id="pi_test_processing",
                status="processing",
                amount_received=0,
                currency="usd",
            )
        ),
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/confirm",
        headers=headers,
    )

    assert response.status_code == 409
    with test_sessions() as db:
        assert db.query(Order).filter(Order.id == order_id).one().status == "pending_payment"
