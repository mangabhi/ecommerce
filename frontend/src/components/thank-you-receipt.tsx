"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { NookLoader } from "@/components/nook-loader";

import {
  ApiError,
  Order,
  Payment,
  Product,
  hasSession,
  orderApi,
  paymentApi,
  productApi,
} from "@/lib/api";

const money = (value: string | number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value));

export default function ThankYouReceipt({ orderId }: { orderId: number }) {
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [products, setProducts] = useState<Record<number, Product>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    async function loadReceipt() {
      if (!hasSession()) {
        router.replace("/login");
        return;
      }
      try {
        const paymentId = Number(
          new URLSearchParams(window.location.search).get("payment_id"),
        );
        let paymentRecord: Payment | null = null;
        if (Number.isInteger(paymentId) && paymentId > 0) {
          for (let attempt = 0; attempt < 10; attempt += 1) {
            try {
              paymentRecord = await paymentApi.confirm(paymentId);
              break;
            } catch (cause) {
              if (!(cause instanceof ApiError && cause.status === 409)) throw cause;
              if (attempt === 9) break;
              await new Promise((resolve) => window.setTimeout(resolve, 1500));
            }
          }
          paymentRecord = await paymentApi.get(paymentId);
        }
        let receipt = await orderApi.get(orderId);
        for (let attempt = 0; receipt.status === "pending_payment" && attempt < 10; attempt += 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 1500));
          receipt = await orderApi.get(orderId);
        }
        if (active) {
          setOrder(receipt);
          setPayment(paymentRecord);
          const productsById: Record<number, Product> = {};
          const productResults = await Promise.all(
            receipt.items.map(async (item) => {
              if (item.product_id === null) return null;
              try {
                return await productApi.get(item.product_id);
              } catch (cause) {
                if (cause instanceof ApiError && cause.status === 404) return null;
                throw cause;
              }
            }),
          );
          for (const product of productResults) {
            if (product) productsById[product.id] = product;
          }
          if (active) setProducts(productsById);
        }
      } catch (cause) {
        if (active) {
          setError(
            cause instanceof ApiError
              ? cause.message
              : cause instanceof Error
                ? cause.message
                : "The order receipt could not be loaded.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadReceipt();
    return () => {
      active = false;
    };
  }, [orderId, retry, router]);

  return (
    <main className="standalone-page">
      <header className="standalone-header">
        <Link className="wordmark" href="/">nook<span>.</span></Link>
        <Link className="quiet-link" href="/">Continue shopping</Link>
      </header>
      <section className="thank-you-page">
        <div className="thank-you-mark" aria-hidden="true">✳</div>
        {loading ? (
          <>
            <p className="eyebrow"><span className="eyebrow-dot" /> CONFIRMING YOUR PAYMENT</p>
            <h1>Just a moment.</h1>
            <p className="thank-you-subtitle">We&apos;re checking that your payment went through securely.</p>
            <NookLoader label="Confirming your payment…" />
          </>
        ) : error || !order ? (
          <>
            <p className="eyebrow"><span className="eyebrow-dot" /> ORDER UPDATE</p>
            <h1>We couldn&apos;t load your receipt.</h1>
            <p className="thank-you-subtitle">{error || "Please open your order history to check its status."}</p>
            <Link className="button button-dark" href="/">Back to the shop</Link>
          </>
        ) : (
          <>
            <p className="eyebrow"><span className="eyebrow-dot" /> ORDER NOOK-{order.id}</p>
            <h1>{order.status === "paid" ? "Thank you." : "Your order is received."}</h1>
            <p className="thank-you-subtitle">
              {order.status === "paid"
                ? "Your payment is confirmed. We can’t wait for these thoughtful finds to reach you."
                : order.status === "pending_payment"
                  ? "Your payment is still being confirmed. If you have completed payment, try checking its status again."
                  : `Your order is ${order.status.replaceAll("_", " ")}. Please review its status before trying to pay again.`}
            </p>
            {order.status === "pending_payment" && (
              <button
                className="button button-outline thank-you-retry"
                onClick={() => {
                  setLoading(true);
                  setError("");
                  setRetry((current) => current + 1);
                }}
              >
                Check payment status again
              </button>
            )}
            <article className="receipt-card">
              <div className="receipt-heading">
                <div><span className="store-overline">YOUR ORDER</span><h2>Order NOOK-{order.id}</h2></div>
                <span className={`status-pill status-${order.status}`}>{order.status.replaceAll("_", " ")}</span>
              </div>
              <div className="receipt-items">
                {order.items.map((item) => (
                  <div className="receipt-item" key={item.id}>
                    <div>
                      <strong>{item.product_name}</strong>
                      <span>Quantity {item.quantity}</span>
                      {item.product_id !== null && products[item.product_id]?.description && (
                        <span className="receipt-product-description">
                          {products[item.product_id].description}
                        </span>
                      )}
                    </div>
                    <strong>{money(Number(item.unit_price) * item.quantity)}</strong>
                  </div>
                ))}
              </div>
              {payment?.payment_method_id && (
                <div className="total-line">
                  <span>Stripe payment method</span>
                  <strong>{payment.payment_method_id}</strong>
                </div>
              )}
              <div className="total-line"><span>Subtotal</span><strong>{money(order.subtotal)}</strong></div>
              {Number(order.discount_amount) > 0 && (
                <div className="total-line total-discount">
                  <span>Coupon {order.coupon_code}</span><strong>−{money(order.discount_amount)}</strong>
                </div>
              )}
              <div className="total-line total-grand">
                <span>{order.status === "paid" ? "Paid total" : "Total"}</span>
                <strong>{money(order.total)}</strong>
              </div>
              <div className="receipt-delivery">
                <h3>Delivering to</h3>
                <p>
                  {[
                    order.shipping_address.recipient_name,
                    order.shipping_address.phone,
                    order.shipping_address.address_line1,
                    order.shipping_address.address_line2,
                    order.shipping_address.city,
                    order.shipping_address.state,
                    order.shipping_address.postal_code,
                    order.shipping_address.country,
                  ].filter(Boolean).join(", ")}
                </p>
              </div>
            </article>
            <div className="thank-you-actions">
              <Link className="button button-dark" href="/">Continue shopping</Link>
              <button className="button button-outline" onClick={() => router.push("/?section=orders")}>View my orders</button>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
