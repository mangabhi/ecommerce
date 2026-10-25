"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { NookLoader } from "@/components/nook-loader";
import {
  Address,
  AddressInput,
  ApiError,
  Cart,
  Order,
  PaymentIntent,
  PaymentConfig,
  UserProfile,
  cartApi,
  couponApi,
  hasSession,
  orderApi,
  paymentApi,
  userApi,
} from "@/lib/api";
import { loadStripe, Stripe } from "@stripe/stripe-js";
import {
  Elements,
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import { FormEvent, useEffect, useState } from "react";

const money = (value: string | number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value));

const blankAddress: AddressInput = {
  label: "home",
  recipient_name: "",
  phone: "",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "",
  postal_code: "",
  country: "",
  is_default: false,
};

function addressFromSaved(address: Address): AddressInput {
  return {
    label: address.label,
    recipient_name: address.recipient_name,
    phone: address.phone,
    address_line1: address.address_line1,
    address_line2: address.address_line2,
    city: address.city,
    state: address.state,
    postal_code: address.postal_code,
    country: address.country,
    is_default: address.is_default,
  };
}

function addressFromOrder(order: Order): AddressInput {
  const shipping = order.shipping_address;
  return {
    ...blankAddress,
    recipient_name: shipping.recipient_name ?? "",
    phone: shipping.phone ?? "",
    address_line1: shipping.address_line1 ?? "",
    address_line2: shipping.address_line2 ?? "",
    city: shipping.city ?? "",
    state: shipping.state ?? "",
    postal_code: shipping.postal_code ?? "",
    country: shipping.country ?? "",
  };
}

export default function CheckoutPage() {
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddress, setSelectedAddress] = useState("");
  const [addressDraft, setAddressDraft] = useState<AddressInput>(blankAddress);
  const [usingNewAddress, setUsingNewAddress] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [paymentIntent, setPaymentIntent] = useState<PaymentIntent | null>(null);
  const [stripePromise, setStripePromise] = useState<Promise<Stripe | null> | null>(null);
  const [paymentConfig, setPaymentConfig] = useState<PaymentConfig | null>(null);
  const [couponCode, setCouponCode] = useState("");
  const [couponDiscount, setCouponDiscount] = useState("0.00");
  const [estimatedTotal, setEstimatedTotal] = useState("0.00");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;
    async function initialize() {
      if (!hasSession()) {
        router.replace("/login");
        return;
      }
      const params = new URLSearchParams(window.location.search);
      const orderId = Number(params.get("order_id"));
      const requestedCoupon = params.get("coupon")?.trim().toUpperCase() ?? "";
      try {
        const [config, nextProfile, nextAddresses] = await Promise.all([
          paymentApi.config(),
          userApi.getProfile(),
          userApi.getAddresses(),
        ]);
        if (!active) return;
        setPaymentConfig(config);
        if (config.enabled && config.publishable_key) {
          setStripePromise(loadStripe(config.publishable_key));
        }
        setProfile(nextProfile);
        setAddresses(nextAddresses);
        setAddressDraft({
          ...blankAddress,
          recipient_name: nextProfile.full_name,
          phone: nextProfile.phone ?? "",
        });

        if (Number.isInteger(orderId) && orderId > 0) {
          const existingOrder = await orderApi.get(orderId);
          if (!active) return;
          if (existingOrder.status !== "pending_payment") {
            setError("This order is no longer waiting for payment.");
          }
          setOrder(existingOrder);
          setAddressDraft(addressFromOrder(existingOrder));
          setEstimatedTotal(existingOrder.total);
        } else {
          const nextCart = await cartApi.get();
          if (!active) return;
          setCart(nextCart);
          setEstimatedTotal(nextCart.subtotal);
          if (!nextCart.items.length) {
            router.replace("/?cart=1");
            return;
          }
          setCouponCode(requestedCoupon);
          if (requestedCoupon) {
            try {
              const quote = await couponApi.quote(requestedCoupon);
              if (!active) return;
              setCouponDiscount(quote.discount_amount);
              setEstimatedTotal(quote.total);
            } catch (cause) {
              if (active) {
                setError(
                  cause instanceof Error
                    ? cause.message
                    : "The coupon could not be applied.",
                );
                setCouponCode("");
              }
            }
          }
          const preferred = nextAddresses.find((address) => address.is_default) ?? nextAddresses[0];
          if (preferred) {
            setSelectedAddress(String(preferred.id));
            setAddressDraft(addressFromSaved(preferred));
          } else {
            setUsingNewAddress(true);
          }
        }
      } catch (cause) {
        if (active) {
          setError(
            cause instanceof ApiError
              ? cause.message
              : cause instanceof Error
                ? cause.message
                : "Checkout could not be loaded.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void initialize();
    return () => {
      active = false;
    };
  }, [router]);

  function selectAddress(value: string) {
    setSelectedAddress(value);
    setUsingNewAddress(value === "new");
    const saved = addresses.find((address) => String(address.id) === value);
    if (saved) setAddressDraft(addressFromSaved(saved));
    if (value === "new") {
      setAddressDraft({
        ...blankAddress,
        recipient_name: profile?.full_name ?? "",
        phone: profile?.phone ?? "",
      });
    }
  }

  async function beginPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await preparePayment();
  }

  async function preparePayment() {
    setError("");
    setSuccess("");
    if (!paymentConfig?.enabled) {
      setError("Stripe is not configured yet. Add Stripe test keys to the backend environment.");
      return;
    }
    if (!order && !usingNewAddress && !selectedAddress) {
      setError("Choose a saved delivery address or enter a new one.");
      return;
    }
    setSubmitting(true);
    try {
      let currentOrder = order;
      if (!currentOrder) {
        let addressId = Number(selectedAddress);
        if (usingNewAddress) {
          const savedAddress = await userApi.createAddress({
            ...addressDraft,
            phone: addressDraft.phone || null,
            address_line2: addressDraft.address_line2 || null,
            is_default: addresses.length === 0 || addressDraft.is_default,
          });
          addressId = savedAddress.id;
          setAddresses((current) => [...current, savedAddress]);
        } else {
          const savedAddress = addresses.find((address) => address.id === addressId);
          if (
            savedAddress &&
            (savedAddress.recipient_name !== addressDraft.recipient_name ||
              savedAddress.phone !== (addressDraft.phone || null))
          ) {
            await userApi.updateAddress(addressId, {
              recipient_name: addressDraft.recipient_name,
              phone: addressDraft.phone || null,
            });
          }
        }
        currentOrder = await orderApi.checkout(addressId, couponCode || null);
        setOrder(currentOrder);
        setEstimatedTotal(currentOrder.total);
        setCouponDiscount(currentOrder.discount_amount);
        setSuccess("Delivery details saved. Complete the secure payment below.");
      }
      const nextIntent = await paymentApi.create(currentOrder.id);
      setPaymentIntent(nextIntent);
      setSuccess("Your order is ready. Enter your card details to complete payment.");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : cause instanceof Error
            ? cause.message
            : "Checkout could not be completed. Please try again.",
      );
      if (order) {
        setSuccess("Your order is saved. You can retry starting its payment below.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <main className="standalone-page"><NookLoader label="Preparing your checkout…" /></main>;
  }

  const itemCount = order
    ? order.items.reduce((total, item) => total + item.quantity, 0)
    : cart?.items.reduce((total, item) => total + item.quantity, 0) ?? 0;
  const subtotal = order?.subtotal ?? cart?.subtotal ?? "0.00";
  const total = order?.total ?? estimatedTotal;
  const discount = order?.discount_amount ?? couponDiscount;

  return (
    <main className="standalone-page">
      <header className="standalone-header">
        <Link className="wordmark" href="/">nook<span>.</span></Link>
        <Link className="quiet-link checkout-back-link" href="/?cart=1">← Back to basket</Link>
      </header>
      <section className="checkout-page">
        <div className="checkout-page-heading">
          <p className="eyebrow"><span className="eyebrow-dot" /> SECURE CHECKOUT</p>
          <h1>Make it yours.</h1>
          <p>Delivery details and a secure Stripe payment, all in one place.</p>
        </div>

        {error && <p className="form-error checkout-notice" role="alert">{error}</p>}
        {success && <p className="form-success checkout-notice" role="status">{success}</p>}

        {!paymentConfig?.enabled && (
          <div className="stripe-setup-notice" role="status">
            <strong>Stripe test mode needs to be configured.</strong>
            <span>Add STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY to the backend, then restart it. Never use test keys for live payments.</span>
          </div>
        )}

        <div className="checkout-page-layout">
          <div className="checkout-details-form">
            {!order ? (
              <form onSubmit={(event) => void beginPayment(event)}>
                <section className="checkout-form-section">
                  <div className="checkout-step-title"><span>01</span><div><h2>Contact information</h2><p>We&apos;ll send your order updates here.</p></div></div>
                  <div className="form-grid">
                    <div className="form-field form-field-wide">
                      <label htmlFor="checkout-email">Email address</label>
                      <input id="checkout-email" type="email" autoComplete="email" value={profile?.email ?? ""} readOnly />
                    </div>
                    <div className="form-field">
                      <label htmlFor="checkout-recipient">Recipient name</label>
                      <input id="checkout-recipient" autoComplete="name" value={addressDraft.recipient_name} onChange={(event) => setAddressDraft({ ...addressDraft, recipient_name: event.target.value })} required />
                    </div>
                    <div className="form-field">
                      <label htmlFor="checkout-phone">Contact phone</label>
                      <input
                        id="checkout-phone"
                        type="tel"
                        autoComplete="tel"
                        value={addressDraft.phone ?? ""}
                        onChange={(event) => setAddressDraft({ ...addressDraft, phone: event.target.value })}
                        required
                      />
                    </div>
                  </div>
                </section>
                <section className="checkout-form-section">
                  <div className="checkout-step-title"><span>02</span><div><h2>Delivery address</h2><p>Choose a saved address or enter a new one.</p></div></div>
                  {addresses.length > 0 && (
                    <div className="form-field checkout-saved-address">
                      <label htmlFor="saved-address">Saved addresses</label>
                      <select
                        id="saved-address"
                        value={usingNewAddress ? "new" : selectedAddress}
                        onChange={(event) => selectAddress(event.target.value)}
                      >
                        {addresses.map((address) => (
                          <option key={address.id} value={address.id}>
                            {address.label} · {address.recipient_name} · {address.address_line1}, {address.city}
                          </option>
                        ))}
                        <option value="new">Enter a new address</option>
                      </select>
                    </div>
                  )}
                  {(usingNewAddress || !addresses.length) && (
                    <div className="form-grid">
                      <div className="form-field">
                        <label htmlFor="delivery-label">Address label</label>
                        <input id="delivery-label" value={addressDraft.label} onChange={(event) => setAddressDraft({ ...addressDraft, label: event.target.value })} />
                      </div>
                      <div className="form-field form-field-wide">
                        <label htmlFor="delivery-line1">Address</label>
                        <input id="delivery-line1" autoComplete="address-line1" required value={addressDraft.address_line1} onChange={(event) => setAddressDraft({ ...addressDraft, address_line1: event.target.value })} />
                      </div>
                      <div className="form-field form-field-wide">
                        <label htmlFor="delivery-line2">Apartment, suite, etc. (optional)</label>
                        <input id="delivery-line2" autoComplete="address-line2" value={addressDraft.address_line2 ?? ""} onChange={(event) => setAddressDraft({ ...addressDraft, address_line2: event.target.value })} />
                      </div>
                      <div className="form-field">
                        <label htmlFor="delivery-city">City</label>
                        <input id="delivery-city" autoComplete="address-level2" required value={addressDraft.city} onChange={(event) => setAddressDraft({ ...addressDraft, city: event.target.value })} />
                      </div>
                      <div className="form-field">
                        <label htmlFor="delivery-state">State / region</label>
                        <input id="delivery-state" autoComplete="address-level1" required value={addressDraft.state} onChange={(event) => setAddressDraft({ ...addressDraft, state: event.target.value })} />
                      </div>
                      <div className="form-field">
                        <label htmlFor="delivery-postal">Postal code</label>
                        <input id="delivery-postal" autoComplete="postal-code" required value={addressDraft.postal_code} onChange={(event) => setAddressDraft({ ...addressDraft, postal_code: event.target.value })} />
                      </div>
                      <div className="form-field">
                        <label htmlFor="delivery-country">Country</label>
                        <input id="delivery-country" autoComplete="country-name" required value={addressDraft.country} onChange={(event) => setAddressDraft({ ...addressDraft, country: event.target.value })} />
                      </div>
                      <label className="checkbox-row form-field-wide">
                        <input type="checkbox" checked={addressDraft.is_default} onChange={(event) => setAddressDraft({ ...addressDraft, is_default: event.target.checked })} />
                        Save as my default address
                      </label>
                    </div>
                  )}
                </section>
                {!paymentIntent && (
                  <button className="button button-dark checkout-continue-button" disabled={submitting || !paymentConfig?.enabled}>
                    {submitting ? "Preparing secure payment…" : "Continue to payment"}
                    <span aria-hidden="true">↗</span>
                  </button>
                )}
              </form>
            ) : (
              <section className="checkout-form-section">
                <div className="checkout-step-title"><span>01</span><div><h2>Delivery details</h2><p>{addressDraft.recipient_name}<br />{addressDraft.address_line1}{addressDraft.address_line2 ? `, ${addressDraft.address_line2}` : ""}<br />{addressDraft.city}, {addressDraft.state} {addressDraft.postal_code} · {addressDraft.country}<br />{addressDraft.phone}</p></div></div>
              </section>
            )}

            {order && paymentIntent && stripePromise && (
              <section className="checkout-form-section checkout-payment-section">
                <div className="checkout-step-title"><span>03</span><div><h2>Payment</h2><p>Card details are securely handled by Stripe.</p></div></div>
                <Elements
                  stripe={stripePromise}
                  options={{
                    clientSecret: paymentIntent.client_secret,
                    appearance: {
                      theme: "stripe",
                      variables: {
                        colorPrimary: "#465641",
                        borderRadius: "3px",
                        fontFamily: "Arial, sans-serif",
                      },
                    },
                  }}
                >
                  <StripePaymentForm
                    order={order}
                    payment={paymentIntent}
                    email={profile?.email ?? ""}
                    address={addressDraft}
                  />
                </Elements>
              </section>
            )}

            {order && !paymentIntent && paymentConfig?.enabled && (
              <button
                className="button button-dark checkout-continue-button"
                type="button"
                disabled={submitting}
                onClick={() => void preparePayment()}
              >
                {submitting ? "Preparing secure payment…" : "Try payment again"}
              </button>
            )}
          </div>

          <aside className="checkout-review-card">
            <p className="store-overline">YOUR ORDER</p>
            <h2>Order summary</h2>
            {(order?.items ?? cart?.items.map((item) => ({
              id: item.id,
              product_id: item.product_id,
              product_name: item.product.name,
              unit_price: item.product.price,
              quantity: item.quantity,
            })) ?? []).map((item) => (
              <div className="checkout-review-item" key={item.id}>
                <span className="checkout-review-quantity">{item.quantity}</span>
                <span>{item.product_name}</span>
                <strong>{money(Number(item.unit_price) * item.quantity)}</strong>
              </div>
            ))}
            <div className="total-line"><span>Items · {itemCount}</span><strong>{money(subtotal)}</strong></div>
            {Number(discount) > 0 && <div className="total-line total-discount"><span>Coupon {order?.coupon_code ?? couponCode}</span><strong>−{money(discount)}</strong></div>}
            <div className="total-line total-shipping"><span>Shipping</span><strong>Calculated at checkout</strong></div>
            <div className="total-line total-grand"><span>Total due</span><strong>{money(total)}</strong></div>
            <p className="checkout-secure-note"><span aria-hidden="true">⌑</span> Secure encrypted payment by Stripe.</p>
          </aside>
        </div>
      </section>
    </main>
  );
}

function StripePaymentForm({
  order,
  payment,
  email,
  address,
}: {
  order: Order;
  payment: PaymentIntent;
  email: string;
  address: AddressInput;
}) {
  const router = useRouter();
  const stripe = useStripe();
  const elements = useElements();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function confirmPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stripe || !elements) return;
    setSubmitting(true);
    setError("");
    try {
      const submitted = await elements.submit();
      if (submitted.error) {
        setError(submitted.error.message ?? "Check your payment details.");
        return;
      }
      const result = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/thank-you/${order.id}?payment_id=${payment.id}`,
          payment_method_data: {
            billing_details: {
              name: address.recipient_name,
              email,
              phone: address.phone || undefined,
            },
          },
        },
        redirect: "if_required",
      });
      if (result.error) {
        setError(result.error.message ?? "The payment could not be completed.");
        return;
      }
      if (result.paymentIntent?.status === "succeeded") {
        await paymentApi.confirm(payment.id);
      }
      router.replace(`/thank-you/${order.id}?payment_id=${payment.id}`);
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : cause instanceof Error
            ? cause.message
            : "The payment could not be confirmed. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="stripe-payment-form" onSubmit={(event) => void confirmPayment(event)}>
      <PaymentElement />
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button button-dark checkout-continue-button" disabled={!stripe || submitting}>
        {submitting ? "Processing payment…" : `Pay ${money(payment.amount)}`}
      </button>
      <p className="checkout-card-note">Your card details are never stored by nook.</p>
    </form>
  );
}
