"use client";

import Link from "next/link";
import { NookLoader } from "@/components/nook-loader";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, Product, cartApi, hasSession, productApi } from "@/lib/api";

const money = (value: string | number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value));

export default function ProductDetails({ productId }: { productId: number }) {
  const router = useRouter();
  const [product, setProduct] = useState<Product | null>(null);
  const [cartCount, setCartCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;
    async function loadProduct() {
      try {
        const found = await productApi.get(productId);
        if (active) setProduct(found);
      } catch (cause) {
        if (active) {
          setError(
            cause instanceof ApiError && cause.status === 404
              ? "This product is no longer available."
              : cause instanceof Error
                ? cause.message
                : "The product could not be loaded.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadProduct();
    if (hasSession()) {
      void cartApi
        .get()
        .then((cart) => {
          if (active) {
            setCartCount(cart.items.reduce((total, item) => total + item.quantity, 0));
          }
        })
        .catch((cause: unknown) => {
          if (active) {
            setError(
              cause instanceof Error
                ? `Product loaded, but basket count could not be checked: ${cause.message}`
                : "Product loaded, but basket count could not be checked.",
            );
          }
        });
    }
    return () => {
      active = false;
    };
  }, [productId]);

  async function addToCart() {
    if (!product) return;
    if (!hasSession()) {
      router.push("/login");
      return;
    }
    setAdding(true);
    setError("");
    setMessage("");
    try {
      const cart = await cartApi.add(product.id, 1);
      setCartCount(cart.items.reduce((total, item) => total + item.quantity, 0));
      setMessage("Added to your basket.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not add this item.");
    } finally {
      setAdding(false);
    }
  }

  if (loading) {
    return <main className="standalone-page"><NookLoader label="Finding this lovely thing…" /></main>;
  }

  if (!product) {
    return (
      <main className="standalone-page">
        <Link className="quiet-link" href="/">← Back to the shop</Link>
        <div className="empty-state">{error || "This product could not be found."}</div>
      </main>
    );
  }

  return (
    <main className="product-page-shell">
      <header className="product-page-header">
        <Link className="wordmark" href="/">nook<span>.</span></Link>
        <Link className="header-cart-button" href="/?cart=1" aria-label={`Open basket, ${cartCount} items`}>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 4h2l2.2 10.1a2 2 0 0 0 2 1.6h8.5a2 2 0 0 0 1.9-1.4L21 8H6" />
            <circle cx="10" cy="20" r="1" />
            <circle cx="18" cy="20" r="1" />
          </svg>
          <span className="header-cart-count">{cartCount > 99 ? "99+" : cartCount}</span>
        </Link>
      </header>
      <div className="product-detail-page">
        <Link className="quiet-link product-back-link" href="/">← Back to the collection</Link>
        <div className="product-detail-layout">
          <div className={`product-detail-image ${product.image_url ? "" : "product-tone-1"}`}>
            {product.image_url ? (
              <span
                className="product-detail-photo"
                role="img"
                aria-label={product.name}
                style={{ backgroundImage: `url("${product.image_url.replaceAll('"', "%22")}")` }}
              />
            ) : (
              <span className="product-detail-placeholder" aria-hidden="true">✳</span>
            )}
          </div>
          <section className="product-detail-copy">
            <p className="store-overline">A THOUGHTFUL FIND</p>
            <h1>{product.name}</h1>
            <p className="product-detail-price">{money(product.price)}</p>
            <p className="product-detail-description">
              {product.description || "A thoughtful piece for everyday living, chosen to bring a little more lovely to your day."}
            </p>
            <p className={`product-availability ${product.stock_quantity > 0 ? "" : "out-of-stock"}`}>
              <span aria-hidden="true">●</span>
              {product.stock_quantity > 0
                ? `${product.stock_quantity} available · ready to ship`
                : "Currently out of stock"}
            </p>
            <button
              className="button button-dark product-add-button"
              disabled={adding || product.stock_quantity < 1}
              onClick={() => void addToCart()}
            >
              {adding ? "Adding…" : product.stock_quantity > 0 ? "Add to basket" : "Out of stock"}
            </button>
            {message && (
              <div className="product-feedback product-feedback-success" role="status">
                <span>{message}</span>
                <Link href="/?cart=1">View basket</Link>
              </div>
            )}
            {error && <p className="form-error product-feedback-error" role="alert">{error}</p>}
            <div className="product-detail-note">
              <span>✳</span>
              <p>Thoughtfully gathered for your everyday rituals.</p>
            </div>
          </section>
        </div>
      </div>
      <footer className="site-footer"><Link className="wordmark" href="/">nook<span>.</span></Link><p>A little more lovely, every day.</p></footer>
    </main>
  );
}
