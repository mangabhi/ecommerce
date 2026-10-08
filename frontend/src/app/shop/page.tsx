"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Address,
  AddressInput,
  ApiError,
  Cart,
  Category,
  Coupon,
  CouponQuote,
  Inventory,
  Notification,
  Order,
  Payment,
  Product,
  ProductInput,
  ProfileInput,
  Review,
  UserProfile,
  authApi,
  cartApi,
  categoryApi,
  clearSession,
  couponApi,
  hasSession,
  inventoryApi,
  notificationApi,
  orderApi,
  paymentApi,
  productApi,
  reviewApi,
  userApi,
  wishlistApi,
} from "@/lib/api";

type Section =
  | "shop"
  | "cart"
  | "orders"
  | "profile"
  | "wishlist"
  | "notifications"
  | "products"
  | "inventory"
  | "coupons"
  | "admin-orders";

const baseAddress: AddressInput = {
  label: "home",
  recipient_name: "",
  phone: null,
  address_line1: "",
  address_line2: null,
  city: "",
  state: "",
  postal_code: "",
  country: "",
  is_default: false,
};

const money = (value: string | number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value));

function errorMessage(cause: unknown) {
  return cause instanceof ApiError
    ? cause.message
    : cause instanceof Error
      ? cause.message
      : "The request could not be completed.";
}

export default function ShopPage() {
  const router = useRouter();
  const [section, setSection] = useState<Section>("shop");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [cart, setCart] = useState<Cart | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [adminOrders, setAdminOrders] = useState<Order[]>([]);
  const [wishlist, setWishlist] = useState<Awaited<ReturnType<typeof wishlistApi.get>>>({ items: [] });
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [lowStock, setLowStock] = useState<Inventory[]>([]);
  const [selectedInventory, setSelectedInventory] = useState<Inventory | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [myReview, setMyReview] = useState<Review | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [quote, setQuote] = useState<CouponQuote | null>(null);
  const [code, setCode] = useState("");
  const [search, setSearch] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sort, setSort] = useState<"created_at" | "name" | "price">("created_at");
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [checkoutAddress, setCheckoutAddress] = useState("");
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewBody, setReviewBody] = useState("");
  const [addressDraft, setAddressDraft] = useState<AddressInput>(baseAddress);
  const [editingAddress, setEditingAddress] = useState<number | null>(null);
  const [profileDraft, setProfileDraft] = useState<ProfileInput>({});
  const [productDraft, setProductDraft] = useState<ProductInput>({
    name: "",
    price: "",
    stock_quantity: 0,
    description: "",
    category_id: null,
    image_url: "",
  });
  const [editingProduct, setEditingProduct] = useState<number | null>(null);
  const [couponDraft, setCouponDraft] = useState({
    code: "",
    discount_type: "percentage" as "percentage" | "fixed",
    discount_value: 10,
    minimum_order_amount: 0,
    maximum_discount: "",
    usage_limit: "",
    starts_at: "",
    expires_at: "",
  });
  const [editingCoupon, setEditingCoupon] = useState<number | null>(null);
  const [inventoryAdjustments, setInventoryAdjustments] = useState<Record<number, string>>({});
  const [inventoryReasons, setInventoryReasons] = useState<Record<number, string>>({});
  const [inventoryChecks, setInventoryChecks] = useState<Record<number, Inventory>>({});
  const [reviewEdit, setReviewEdit] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const isAdmin = profile?.role === "admin";
  const itemCount = useMemo(
    () => cart?.items.reduce((total, item) => total + item.quantity, 0) ?? 0,
    [cart],
  );

  const loadPrivate = useCallback(async () => {
    if (!hasSession()) return;
    const [nextProfile, nextCart, nextAddresses, nextOrders, nextWishlist, nextNotifications] =
      await Promise.all([
        userApi.getProfile(),
        cartApi.get(),
        userApi.getAddresses(),
        orderApi.list(),
        wishlistApi.get(),
        notificationApi.list(),
      ]);
    setProfile(nextProfile);
    setProfileDraft({
      full_name: nextProfile.full_name,
      phone: nextProfile.phone,
      date_of_birth: nextProfile.date_of_birth,
      avatar_url: nextProfile.avatar_url,
    });
    setCart(nextCart);
    setAddresses(nextAddresses);
    setOrders(nextOrders);
    setWishlist(nextWishlist);
    setNotifications(nextNotifications);
    const preferredAddress = nextAddresses.find((address) => address.is_default) ?? nextAddresses[0];
    setCheckoutAddress(preferredAddress ? String(preferredAddress.id) : "");
  }, []);

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const [nextProducts, nextCategories] = await Promise.all([
          productApi.list({ sort_by: "created_at", order: "desc" }),
          categoryApi.list(),
        ]);
        if (!active) return;
        setProducts(nextProducts);
        setCategories(nextCategories);
        if (hasSession()) {
          await loadPrivate();
        }
      } catch (cause) {
        if (cause instanceof ApiError && cause.status === 401) {
          clearSession();
          setProfile(null);
          return;
        }
        if (active) setError(errorMessage(cause));
      } finally {
        if (active) setLoading(false);
      }
    }
    void initialize();
    return () => {
      active = false;
    };
  }, [loadPrivate]);

  async function perform<T>(
    request: () => Promise<T>,
    success?: string,
  ): Promise<T | undefined> {
    setError("");
    setMessage("");
    setWorking(true);
    try {
      const result = await request();
      if (success) setMessage(success);
      return result;
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        clearSession();
        setProfile(null);
      }
      setError(errorMessage(cause));
      return undefined;
    } finally {
      setWorking(false);
    }
  }

  async function openProduct(productId: number) {
    const product = await perform(() => productApi.get(productId));
    if (!product) return;
    setSelectedProduct(product);
    setReviewEdit(false);
    const found = await perform(() => reviewApi.list(productId));
    if (found) {
      setReviews(found);
      setMyReview(found.find((review) => review.user_id === profile?.user_id) ?? null);
    }
    const stock = await perform(() => inventoryApi.get(productId));
    if (stock) setSelectedInventory(stock);
  }

  async function changeSection(next: Section) {
    setSection(next);
    setError("");
    setMessage("");
    if (!hasSession() && next !== "shop") {
      router.push("/login");
      return;
    }
    if (!isAdmin && ["products", "inventory", "coupons", "admin-orders"].includes(next)) {
      setSection("shop");
      setError("This section is available to administrators only.");
      return;
    }
    if (next === "cart") {
      const found = await perform(() => cartApi.get());
      if (found) setCart(found);
    } else if (next === "orders") {
      const found = await perform(() => orderApi.list());
      if (found) setOrders(found);
    } else if (next === "wishlist") {
      const found = await perform(() => wishlistApi.get());
      if (found) setWishlist(found);
    } else if (next === "notifications") {
      const found = await perform(() => notificationApi.list());
      if (found) setNotifications(found);
    } else if (next === "products") {
      const found = await perform(() => productApi.list());
      if (found) setProducts(found);
    } else if (next === "inventory") {
      const found = await perform(() => inventoryApi.lowStock());
      if (found) setLowStock(found);
    } else if (next === "coupons") {
      const found = await perform(() => couponApi.list());
      if (found) setCoupons(found);
    } else if (next === "admin-orders") {
      const found = await perform(() => orderApi.adminList());
      if (found) setAdminOrders(found);
    } else if (next === "profile") {
      await perform(loadPrivate);
    }
  }

  async function refreshCart() {
    const found = await cartApi.get();
    setCart(found);
  }

  async function addToCart(productId: number) {
    if (!hasSession()) {
      router.push("/login");
      return;
    }
    const found = await perform(() => cartApi.add(productId, 1), "Added to your basket.");
    if (found) setCart(found);
  }

  async function toggleWishlist(productId: number) {
    if (!hasSession()) {
      router.push("/login");
      return;
    }
    const exists = wishlist.items.some((item) => item.product_id === productId);
    const found = exists
      ? await perform(async () => {
          await wishlistApi.remove(productId);
          return wishlistApi.get();
        }, "Removed from your saved pieces.")
      : await perform(() => wishlistApi.add(productId), "Saved for later.");
    if (found) setWishlist(found);
  }

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProduct) return;
    const input = { rating: reviewRating, title: reviewTitle || undefined, body: reviewBody || undefined };
    const saved = myReview
      ? await perform(() => reviewApi.update(myReview.id, input), "Your review was updated.")
      : await perform(() => reviewApi.create(selectedProduct.id, input), "Thank you for your review.");
    if (!saved) return;
    setReviewEdit(false);
    const found = await reviewApi.list(selectedProduct.id);
    setReviews(found);
    setMyReview(found.find((review) => review.user_id === profile?.user_id) ?? null);
  }

  async function removeReview() {
    if (!myReview) return;
    const removed = await perform(async () => {
      await reviewApi.remove(myReview.id);
      return true;
    }, "Your review was removed.");
    if (removed) {
      setReviews((current) => current.filter((review) => review.id !== myReview.id));
      setMyReview(null);
      setReviewEdit(false);
    }
  }

  async function applyQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await perform(() => couponApi.quote(code || null));
    if (result) setQuote(result);
  }

  async function validateCoupon() {
    if (!cart) return;
    const result = await perform(() => couponApi.validate(code, cart.subtotal));
    if (result) setQuote(result);
  }

  async function checkout(useCreateOrder = false) {
    if (!checkoutAddress) {
      setError("Add or choose a delivery address before checking out.");
      return;
    }
    const created = await perform(
      () =>
        useCreateOrder
          ? orderApi.create(Number(checkoutAddress), code || null)
          : orderApi.checkout(Number(checkoutAddress), code || null),
      "Order placed. Complete payment to confirm it.",
    );
    if (!created) return;
    setSelectedOrder(created);
    setOrders((current) => [created, ...current]);
    await refreshCart();
    setSection("orders");
  }

  async function beginPayment(order: Order) {
    const created = await perform(() => paymentApi.create(order.id), "Mock payment created.");
    if (created) {
      setPayment(created);
      setSelectedOrder(order);
    }
  }

  async function completeMockPayment(status: "succeeded" | "failed") {
    if (!payment) return;
    const result = await perform(
      () =>
        paymentApi.webhook({
          provider_reference: payment.provider_reference,
          status,
          amount: payment.amount,
        }),
      status === "succeeded" ? "Payment completed." : "Payment failed; stock was released.",
    );
    if (!result) return;
    setPayment(result);
    const fresh = await orderApi.get(result.order_id);
    setSelectedOrder(fresh);
    setOrders((current) => current.map((order) => (order.id === fresh.id ? fresh : order)));
  }

  async function cancelOrder(order: Order) {
    const result = await perform(
      () => orderApi.cancel(order.id, "Cancellation requested by customer."),
      "Cancellation request submitted.",
    );
    if (!result) return;
    setSelectedOrder(result);
    setOrders((current) => current.map((item) => (item.id === result.id ? result : item)));
  }

  async function loadOrder(orderId: number) {
    const [found, tracking] = await Promise.all([
      orderApi.get(orderId),
      orderApi.tracking(orderId),
    ]).catch((cause: unknown) => {
      setError(errorMessage(cause));
      return [null, null] as const;
    });
    if (found) {
      setSelectedOrder({
        ...found,
        tracking_number: tracking?.tracking_number ?? found.tracking_number,
        tracking_status: tracking?.tracking_status ?? found.tracking_status,
      });
    }
  }

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const saved = await perform(() => userApi.updateProfile(profileDraft), "Your details are saved.");
    if (saved) setProfile(saved);
  }

  async function submitAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const saved = await perform(
      () =>
        editingAddress
          ? userApi.updateAddress(editingAddress, addressDraft)
          : userApi.createAddress(addressDraft),
      editingAddress ? "Address updated." : "Address saved.",
    );
    if (!saved) return;
    const next = editingAddress
      ? addresses.map((address) => (address.id === saved.id ? saved : address))
      : [...addresses, saved];
    setAddresses(
      saved.is_default
        ? next.map((address) => ({ ...address, is_default: address.id === saved.id }))
        : next,
    );
    setAddressDraft(baseAddress);
    setEditingAddress(null);
  }

  async function removeAddress(address: Address) {
    const removed = await perform(async () => {
      await userApi.deleteAddress(address.id);
      return true;
    }, "Address removed.");
    if (removed) {
      setAddresses((current) => current.filter((item) => item.id !== address.id));
    }
  }

  async function submitProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload: ProductInput = {
      ...productDraft,
      price: String(productDraft.price),
      stock_quantity: Number(productDraft.stock_quantity ?? 0),
      category_id: productDraft.category_id ? Number(productDraft.category_id) : null,
      description: productDraft.description || null,
      image_url: productDraft.image_url || null,
    };
    const saved = await perform(
      () =>
        editingProduct
          ? productApi.update(editingProduct, payload)
          : productApi.create(payload),
      editingProduct ? "Product updated." : "Product created.",
    );
    if (!saved) return;
    setProducts((current) =>
      editingProduct
        ? current.map((product) => (product.id === saved.id ? saved : product))
        : [saved, ...current],
    );
    setProductDraft({
      name: "",
      price: "",
      stock_quantity: 0,
      description: "",
      category_id: null,
      image_url: "",
    });
    setEditingProduct(null);
  }

  async function archiveProduct(product: Product) {
    const removed = await perform(async () => {
      await productApi.archive(product.id);
      return true;
    }, "Product archived.");
    if (removed) setProducts((current) => current.filter((item) => item.id !== product.id));
  }

  async function adjustStock(productId: number) {
    const change = Number(inventoryAdjustments[productId] ?? "");
    if (!Number.isInteger(change) || change === 0) {
      setError("Enter a non-zero whole-number stock adjustment.");
      return;
    }
    const adjusted = await perform(
      () => inventoryApi.adjust(productId, change, inventoryReasons[productId] || null),
      "Stock updated.",
    );
    if (!adjusted) return;
    const next = await inventoryApi.lowStock();
    setLowStock(next);
  }

  async function submitCoupon(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      discount_type: couponDraft.discount_type,
      discount_value: Number(couponDraft.discount_value),
      minimum_order_amount: Number(couponDraft.minimum_order_amount),
      maximum_discount: couponDraft.maximum_discount
        ? Number(couponDraft.maximum_discount)
        : null,
      usage_limit: couponDraft.usage_limit ? Number(couponDraft.usage_limit) : null,
      starts_at: couponDraft.starts_at
        ? new Date(couponDraft.starts_at).toISOString()
        : null,
      expires_at: couponDraft.expires_at
        ? new Date(couponDraft.expires_at).toISOString()
        : null,
    };
    const saved = await perform(
      () =>
        editingCoupon
          ? couponApi.update(editingCoupon, payload)
          : couponApi.create({ ...payload, code: couponDraft.code }),
      editingCoupon ? "Coupon updated." : "Coupon created.",
    );
    if (saved) {
      setCoupons((current) =>
        editingCoupon
          ? current.map((coupon) => coupon.id === saved.id ? saved : coupon)
          : [saved, ...current],
      );
      setCouponDraft({
        code: "",
        discount_type: "percentage",
        discount_value: 10,
        minimum_order_amount: 0,
        maximum_discount: "",
        usage_limit: "",
        starts_at: "",
        expires_at: "",
      });
      setEditingCoupon(null);
    }
  }

  async function toggleCoupon(coupon: Coupon) {
    const saved = await perform(
      () => couponApi.update(coupon.id, { is_active: !coupon.is_active }),
      coupon.is_active ? "Coupon disabled." : "Coupon enabled.",
    );
    if (saved) setCoupons((current) => current.map((item) => item.id === saved.id ? saved : item));
  }

  async function setAdminStatus(order: Order, status: "processing" | "shipped" | "delivered" | "cancelled") {
    const tracking = window.prompt(
      "Tracking number (leave blank to keep the existing one):",
      order.tracking_number ?? "",
    );
    if (tracking === null) return;
    const saved = await perform(
      () =>
        orderApi.adminUpdate(order.id, {
          status,
          ...(tracking ? { tracking_number: tracking } : {}),
          tracking_status: status,
        }),
      `Order #${order.id} updated.`,
    );
    if (saved) setAdminOrders((current) => current.map((item) => item.id === saved.id ? saved : item));
  }

  async function markRead(notification: Notification) {
    const saved = await perform(() => notificationApi.markRead(notification.id), "Notification marked read.");
    if (saved) {
      setNotifications((current) => current.map((item) => item.id === saved.id ? saved : item));
    }
  }

  async function sendTestNotification() {
    const created = await perform(
      () => notificationApi.createTest("A little hello", "Your development test notification is working."),
      "Test notification created.",
    );
    if (created) setNotifications((current) => [created, ...current]);
  }

  async function logout() {
    const signedOut = await perform(async () => {
      await authApi.logout();
      return true;
    }, "Signed out.");
    if (!signedOut) return;
    clearSession();
    setProfile(null);
    router.push("/");
  }

  if (loading) {
    return <div className="loading-state">Opening the nook shop…</div>;
  }

  const navItems: { id: Section; label: string; icon: string }[] = [
    { id: "shop", label: "Discover", icon: "✳" },
    { id: "cart", label: `Your basket${itemCount ? ` · ${itemCount}` : ""}`, icon: "◌" },
    { id: "orders", label: "Orders", icon: "↗" },
    { id: "wishlist", label: "Saved pieces", icon: "♡" },
    { id: "profile", label: "Your account", icon: "◡" },
    { id: "notifications", label: "Notifications", icon: "✉" },
  ];

  return (
    <main className="store-shell">
      <div className="announcement">
        Thoughtful things for everyday living <span aria-hidden="true">✳</span>
      </div>
      <header className="site-header store-header">
        <Link className="wordmark" href="/" aria-label="Nook home">nook<span>.</span></Link>
        <nav className="header-nav" aria-label="Store navigation">
          <button className="text-link" onClick={() => void changeSection("shop")}>Shop</button>
          <button className="text-link" onClick={() => void changeSection("orders")}>Orders</button>
          <button className="text-link" onClick={() => void changeSection("wishlist")}>Wishlist</button>
        </nav>
        <div className="header-actions">
          {profile ? (
            <>
              <span className="store-greeting">Hello, {profile.full_name.split(" ")[0]}</span>
              <button className="button button-outline button-small" onClick={() => void logout()}>Sign out</button>
            </>
          ) : (
            <>
              <Link className="text-link" href="/login">Sign in</Link>
              <Link className="button button-dark button-small" href="/register">Join nook <span aria-hidden="true">↗</span></Link>
            </>
          )}
        </div>
      </header>

      <div className="store-layout">
        <aside className="store-sidebar">
          <p className="store-overline">YOUR LITTLE CORNER</p>
          <nav aria-label="Store sections">
            {navItems.map((item) => (
              <button
                className={`store-nav-item ${section === item.id ? "active" : ""}`}
                key={item.id}
                onClick={() => void changeSection(item.id)}
              >
                <span aria-hidden="true">{item.icon}</span>{item.label}
                {item.id === "notifications" && notifications.some((notice) => !notice.is_read) && <i />}
              </button>
            ))}
          </nav>
          {isAdmin && (
            <>
              <p className="store-overline admin-overline">STUDIO</p>
              {([
                ["products", "Products"],
                ["inventory", "Inventory"],
                ["coupons", "Coupons"],
                ["admin-orders", "Manage orders"],
              ] as const).map(([id, label]) => (
                <button
                  className={`store-nav-item ${section === id ? "active" : ""}`}
                  key={id}
                  onClick={() => void changeSection(id)}
                >
                  <span aria-hidden="true">◇</span>{label}
                </button>
              ))}
            </>
          )}
          <div className="sidebar-note">
            <span aria-hidden="true">✳</span>
            <p>A more considered kind of everyday.</p>
          </div>
        </aside>

        <section className="store-main">
          {error && <p className="form-error store-alert" role="alert">{error}</p>}
          {message && <p className="form-success store-alert" role="status">{message}</p>}

          {section === "shop" && (
            <>
              <div className="store-welcome">
                <div>
                  <p className="eyebrow"><span className="eyebrow-dot" /> THE GOOD THINGS, GATHERED</p>
                  <h1>Make room for<br /><em>the everyday.</em></h1>
                  <p>Thoughtful finds for the little rituals that make a day.</p>
                </div>
                <div className="welcome-bloom" aria-hidden="true">✳</div>
              </div>
              <div className="store-section-head">
                <div>
                  <p className="store-overline">A FEW GOOD THINGS</p>
                  <h2>Find your <em>favourite.</em></h2>
                </div>
                <span>{products.length} pieces</span>
              </div>
              <form
                className="catalog-tools"
                onSubmit={async (event) => {
                  event.preventDefault();
                  setCategoryId(null);
                  const found = await perform(() => productApi.list({
                    search: search || undefined,
                    min_price: minPrice || undefined,
                    max_price: maxPrice || undefined,
                    sort_by: sort,
                    order: sort === "created_at" ? "desc" : "asc",
                  }));
                  if (found) setProducts(found);
                }}
              >
                <input aria-label="Search products" placeholder="Search the collection…" value={search} onChange={(event) => setSearch(event.target.value)} />
                <input aria-label="Minimum price" type="number" min="0" placeholder="Min price" value={minPrice} onChange={(event) => setMinPrice(event.target.value)} />
                <input aria-label="Maximum price" type="number" min="0" placeholder="Max price" value={maxPrice} onChange={(event) => setMaxPrice(event.target.value)} />
                <select aria-label="Sort products" value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}>
                  <option value="created_at">Recently added</option>
                  <option value="name">Name</option>
                  <option value="price">Price</option>
                </select>
                <button className="button button-dark" type="submit">Find pieces</button>
              </form>
              {categories.length > 0 && (
                <div className="category-chips" aria-label="Categories">
                  <button
                    className={!categoryId ? "selected" : ""}
                    onClick={async () => {
                      setCategoryId(null);
                      const found = await perform(() => productApi.list({
                        search: search || undefined,
                        min_price: minPrice || undefined,
                        max_price: maxPrice || undefined,
                        sort_by: sort,
                        order: sort === "created_at" ? "desc" : "asc",
                      }));
                      if (found) setProducts(found);
                    }}
                  >
                    All pieces
                  </button>
                  {categories.map((category) => (
                    <button
                      className={categoryId === category.id ? "selected" : ""}
                      key={category.id}
                      onClick={async () => {
                        setCategoryId(category.id);
                        const found = await perform(() => categoryApi.products(category.id));
                        if (found) setProducts(found);
                      }}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              )}
              {products.length ? (
                <div className="product-grid">
                  {products.map((product, index) => (
                    <article className="product-card" key={product.id}>
                      <button className={`product-image product-tone-${index % 4}`} onClick={() => void openProduct(product.id)} aria-label={`View ${product.name}`}>
                        {product.image_url ? <span className="product-photo" aria-hidden="true" style={{ backgroundImage: `url("${product.image_url.replaceAll('"', "%22")}")` }} /> : <span aria-hidden="true">{["✳", "◌", "✿", "◇"][index % 4]}</span>}
                        <small>{product.stock_quantity > 0 ? "READY TO SHIP" : "A LITTLE WAIT"}</small>
                      </button>
                      <div className="product-card-info">
                        <div>
                          <button className="product-name" onClick={() => void openProduct(product.id)}>{product.name}</button>
                          <p>{product.description || categories.find((category) => category.id === product.category_id)?.name || "A thoughtful everyday find"}</p>
                        </div>
                        <span>{money(product.price)}</span>
                      </div>
                      <div className="product-card-actions">
                        <button className="button button-dark" disabled={!product.stock_quantity || working} onClick={() => void addToCart(product.id)}>
                          {product.stock_quantity ? "Add to basket" : "Out of stock"}
                        </button>
                        <button className="icon-button" aria-label="Save product" onClick={() => void toggleWishlist(product.id)}>
                          {wishlist.items.some((item) => item.product_id === product.id) ? "♥" : "♡"}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state">No pieces found just now. Try a different search or category.</div>
              )}
              {selectedProduct && (
                <section className="panel product-detail" id="product-detail">
                  <div className="panel-heading">
                    <div><p className="store-overline">A CLOSER LOOK</p><h2>{selectedProduct.name}</h2></div>
                    <button className="small-action" onClick={() => setSelectedProduct(null)}>Close</button>
                  </div>
                  <p>{selectedProduct.description || "A thoughtful piece for everyday living."}</p>
                  <div className="detail-price">{money(selectedProduct.price)} <span>{selectedInventory?.stock_quantity ?? selectedProduct.stock_quantity} in stock</span></div>
                  <div className="product-card-actions">
                    <button className="button button-dark" onClick={() => void addToCart(selectedProduct.id)}>Add to basket</button>
                    <button className="button button-outline" onClick={() => void toggleWishlist(selectedProduct.id)}>Save for later</button>
                  </div>
                  <div className="review-area">
                    <div className="panel-heading">
                      <div><h3>Notes from the nook</h3><p>{reviews.length} {reviews.length === 1 ? "review" : "reviews"}</p></div>
                    </div>
                    {reviews.map((review) => (
                      <article className="review-card" key={review.id}>
                        <div><strong>{review.reviewer_name}</strong><span>{"★".repeat(review.rating)}{"☆".repeat(5 - review.rating)}</span></div>
                        {review.title && <h4>{review.title}</h4>}
                        {review.body && <p>{review.body}</p>}
                        {review.user_id === profile?.user_id && <div className="inline-actions"><button className="small-action" onClick={() => { setReviewRating(review.rating); setReviewTitle(review.title ?? ""); setReviewBody(review.body ?? ""); setReviewEdit(true); }}>Edit yours</button><button className="small-action danger" onClick={() => void removeReview()}>Delete</button></div>}
                      </article>
                    ))}
                    {profile && (reviewEdit || !myReview) && (
                      <form className="form-grid review-form" onSubmit={(event) => void submitReview(event)}>
                        <div className="form-field"><label htmlFor="review-rating">Rating</label><select id="review-rating" value={reviewRating} onChange={(event) => setReviewRating(Number(event.target.value))}>{[5,4,3,2,1].map((rating) => <option key={rating} value={rating}>{rating} stars</option>)}</select></div>
                        <div className="form-field"><label htmlFor="review-title">Title</label><input id="review-title" value={reviewTitle} onChange={(event) => setReviewTitle(event.target.value)} maxLength={255} /></div>
                        <div className="form-field form-field-wide"><label htmlFor="review-body">Your note</label><textarea id="review-body" value={reviewBody} onChange={(event) => setReviewBody(event.target.value)} maxLength={5000} /></div>
                        <div className="form-actions"><button className="button button-dark" disabled={working}>{myReview ? "Save review" : "Leave a review"}</button>{reviewEdit && <button type="button" className="button button-plain" onClick={() => setReviewEdit(false)}>Cancel</button>}</div>
                      </form>
                    )}
                    {!profile && <p className="muted-copy"><Link href="/login">Sign in</Link> to leave a review.</p>}
                  </div>
                </section>
              )}
            </>
          )}

          {section === "cart" && (
            <section className="store-page-section">
              <SectionTitle overline="ALMOST YOURS" title="Your basket." subtitle="A few lovely things, all in one place." />
              {!cart?.items.length ? <div className="empty-state"><p>Your basket is waiting for something good.</p><button className="button button-dark" onClick={() => void changeSection("shop")}>Explore the collection</button></div> : (
                <div className="cart-layout">
                  <div className="cart-items">
                    {cart.items.map((item) => (
                      <article className="cart-row" key={item.id}>
                        <div className="cart-item-mark">✳</div>
                        <div className="cart-item-copy"><h3>{item.product.name}</h3><p>{money(item.product.price)} each</p></div>
                        <div className="quantity-control">
                          <button aria-label="Decrease quantity" disabled={working || item.quantity <= 1} onClick={async () => { const updated = await perform(() => cartApi.update(item.id, item.quantity - 1)); if (updated) setCart(updated); }}>−</button>
                          <span>{item.quantity}</span>
                          <button aria-label="Increase quantity" disabled={working || item.quantity >= item.product.stock_quantity} onClick={async () => { const updated = await perform(() => cartApi.update(item.id, item.quantity + 1)); if (updated) setCart(updated); }}>+</button>
                        </div>
                        <strong>{money(item.subtotal)}</strong>
                        <button className="small-action danger" onClick={async () => { const updated = await perform(() => cartApi.remove(item.id), "Item removed."); if (updated) setCart(updated); }}>Remove</button>
                      </article>
                    ))}
                    <button className="small-action danger" onClick={async () => { const cleared = await perform(async () => { await cartApi.clear(); return true; }, "Basket cleared."); if (cleared) setCart(await cartApi.get()); }}>Clear basket</button>
                  </div>
                  <aside className="checkout-card">
                    <h3>A little total-up</h3>
                    <form className="coupon-row" onSubmit={(event) => void applyQuote(event)}>
                      <input aria-label="Coupon code" placeholder="Have a little code?" value={code} onChange={(event) => setCode(event.target.value)} />
                      <button className="button button-outline" type="submit">Apply</button>
                    </form>
                    <button className="small-action coupon-validate" onClick={() => void validateCoupon()}>Validate code</button>
                    <div className="total-line"><span>Subtotal</span><strong>{money(cart.subtotal)}</strong></div>
                    {quote && <><div className="total-line"><span>Code {quote.coupon_code ?? ""}</span><strong>−{money(quote.discount_amount)}</strong></div><div className="total-line total-grand"><span>Estimated total</span><strong>{money(quote.total)}</strong></div></>}
                    <label className="form-field checkout-address"><span>Deliver to</span><select value={checkoutAddress} onChange={(event) => setCheckoutAddress(event.target.value)}><option value="">Choose an address</option>{addresses.map((address) => <option key={address.id} value={address.id}>{address.label} · {address.address_line1}, {address.city}</option>)}</select></label>
                    {!addresses.length && <button className="small-action" onClick={() => void changeSection("profile")}>Add a delivery address</button>}
                    <button className="button button-dark checkout-button" disabled={working || !cart.items.length} onClick={() => void checkout(false)}>Continue to checkout <span aria-hidden="true">↗</span></button>
                    <button className="button button-outline checkout-button" disabled={working || !cart.items.length} onClick={() => void checkout(true)}>Create order directly</button>
                    <p className="muted-copy">Stock is checked again when your order is placed.</p>
                  </aside>
                </div>
              )}
            </section>
          )}

          {section === "orders" && (
            <section className="store-page-section">
              <SectionTitle overline="THE GOOD THINGS ARE ON THEIR WAY" title="Your orders." subtitle="Follow every order from checkout to your door." />
              {!orders.length ? <div className="empty-state">Your order history will find a home here.</div> : (
                <div className="order-list">
                  {orders.map((order) => (
                    <article className="order-card" key={order.id}>
                      <div className="order-card-head"><div><span className="store-overline">ORDER NOOK-{order.id}</span><h3>{new Date(order.created_at).toLocaleDateString()}</h3></div><span className={`status-pill status-${order.status}`}>{order.status.replaceAll("_", " ")}</span></div>
                      <p>{order.items.map((item) => `${item.product_name} × ${item.quantity}`).join(" · ")}</p>
                      <div className="order-card-foot"><strong>{money(order.total)}</strong><div className="inline-actions">
                        <button className="small-action" onClick={() => void loadOrder(order.id)}>Details & tracking</button>
                        {order.status === "pending_payment" && <button className="small-action" onClick={() => void beginPayment(order)}>Pay now</button>}
                        {["pending_payment","paid","processing"].includes(order.status) && <button className="small-action danger" onClick={() => void cancelOrder(order)}>Cancel</button>}
                      </div></div>
                    </article>
                  ))}
                </div>
              )}
              {selectedOrder && <section className="panel selected-order">
                <div className="panel-heading"><div><p className="store-overline">ORDER NOOK-{selectedOrder.id}</p><h2>Order details & tracking</h2></div><button className="small-action" onClick={() => setSelectedOrder(null)}>Close</button></div>
                <p className="status-pill">{selectedOrder.status.replaceAll("_", " ")}</p>
                {selectedOrder.tracking_number && <p>Tracking {selectedOrder.tracking_number} · {selectedOrder.tracking_status || "Tracking number assigned"}</p>}
                <ul>{selectedOrder.items.map((item) => <li key={item.id}>{item.product_name} × {item.quantity} — {money(item.unit_price)}</li>)}</ul>
                <p>Shipping to: {Object.values(selectedOrder.shipping_address).filter(Boolean).join(", ")}</p>
                {payment && payment.order_id === selectedOrder.id && <div className="payment-card"><strong>Mock payment {payment.status}</strong><p>{payment.currency} {money(payment.amount)} · ref {payment.provider_reference}</p><div className="inline-actions"><button className="small-action" onClick={async () => {const current = await perform(() => paymentApi.get(payment.id)); if (current) setPayment(current);}}>Refresh status</button>{payment.status === "pending" && process.env.NODE_ENV === "development" && <><button className="button button-dark" onClick={() => void completeMockPayment("succeeded")}>Simulate success</button><button className="button button-plain" onClick={() => void completeMockPayment("failed")}>Simulate failure</button></>}{payment.status === "succeeded" && <button className="small-action danger" onClick={async () => { const refunded = await perform(() => paymentApi.refund(payment.id, "Refund requested by customer."), "Refund completed."); if (refunded) setPayment(refunded); }}>Request refund</button>}</div></div>}
              </section>}
            </section>
          )}

          {section === "profile" && (
            <section className="store-page-section">
              <SectionTitle overline="YOUR LITTLE CORNER" title={`Hello, ${profile?.full_name.split(" ")[0] ?? "there"}.`} subtitle="Your details and favourite places, ready when you need them." />
              {!profile ? <div className="empty-state"><Link href="/login">Sign in</Link> to manage your account.</div> : (
                <>
                  <section className="panel">
                    <div className="panel-heading"><div><h2>Personal details</h2><p>Your email and account type stay safely read-only.</p></div></div>
                    <form className="form-grid" onSubmit={(event) => void submitProfile(event)}>
                      <div className="form-field form-field-wide"><label>Email</label><input value={profile.email} readOnly /></div>
                      <div className="form-field"><label htmlFor="name">Full name</label><input id="name" required minLength={2} maxLength={255} value={profileDraft.full_name ?? ""} onChange={(event) => setProfileDraft({ ...profileDraft, full_name: event.target.value })} /></div>
                      <div className="form-field"><label htmlFor="phone">Phone</label><input id="phone" type="tel" maxLength={20} value={profileDraft.phone ?? ""} onChange={(event) => setProfileDraft({ ...profileDraft, phone: event.target.value || null })} /></div>
                      <div className="form-field"><label htmlFor="birthday">Date of birth</label><input id="birthday" type="date" value={profileDraft.date_of_birth ?? ""} onChange={(event) => setProfileDraft({ ...profileDraft, date_of_birth: event.target.value || null })} /></div>
                      <div className="form-field"><label htmlFor="avatar">Avatar URL</label><input id="avatar" type="url" value={profileDraft.avatar_url ?? ""} onChange={(event) => setProfileDraft({ ...profileDraft, avatar_url: event.target.value || null })} /></div>
                      <div className="form-actions form-field-wide"><button className="button button-dark" disabled={working}>Save details</button><span className="muted-copy">Account role: {profile.role}</span></div>
                    </form>
                  </section>
                  <section className="panel">
                    <div className="panel-heading"><div><h2>Saved addresses</h2><p>Pick a delivery spot or add somewhere new.</p></div></div>
                    <div className="address-list">
                      {addresses.map((address) => <article className="address-card" key={address.id}>
                        <div className="address-card-top"><span className="address-label">{address.label}</span>{address.is_default && <span className="default-label">Default</span>}</div>
                        <h3>{address.recipient_name}</h3><p>{address.address_line1}{address.address_line2 ? `, ${address.address_line2}` : ""}<br />{address.city}, {address.state} {address.postal_code}<br />{address.country}{address.phone ? ` · ${address.phone}` : ""}</p>
                        <div className="address-actions"><button className="small-action" onClick={() => {setEditingAddress(address.id); setAddressDraft({ label:address.label, recipient_name:address.recipient_name, phone:address.phone, address_line1:address.address_line1, address_line2:address.address_line2, city:address.city, state:address.state, postal_code:address.postal_code, country:address.country, is_default:address.is_default });}}>Edit</button><button className="small-action danger" onClick={() => void removeAddress(address)}>Remove</button></div>
                      </article>)}
                    </div>
                    <form className="form-grid address-editor" onSubmit={(event) => void submitAddress(event)}>
                      <h3 className="form-field-wide">{editingAddress ? "Edit address" : "Add a saved address"}</h3>
                      {([
                        ["label", "Label"], ["recipient_name", "Recipient name"], ["phone", "Phone"],
                        ["address_line1", "Address line 1"], ["address_line2", "Address line 2"],
                        ["city", "City"], ["state", "State / region"], ["postal_code", "Postal code"], ["country", "Country"],
                      ] as const).map(([field, label]) => (
                        <div className="form-field" key={field}><label htmlFor={`address-${field}`}>{label}</label><input id={`address-${field}`} required={["label","recipient_name","address_line1","city","state","postal_code","country"].includes(field)} value={addressDraft[field] ?? ""} onChange={(event) => setAddressDraft({ ...addressDraft, [field]: event.target.value || (field === "phone" || field === "address_line2" ? null : "") })} /></div>
                      ))}
                      <label className="checkbox-row form-field-wide"><input type="checkbox" checked={addressDraft.is_default} onChange={(event) => setAddressDraft({ ...addressDraft, is_default: event.target.checked })} /> Make this my default address</label>
                      <div className="form-actions form-field-wide"><button className="button button-dark" disabled={working}>{editingAddress ? "Save address" : "Add address"}</button>{editingAddress && <button type="button" className="button button-plain" onClick={() => {setEditingAddress(null);setAddressDraft(baseAddress);}}>Cancel</button>}</div>
                    </form>
                  </section>
                </>
              )}
            </section>
          )}

          {section === "wishlist" && (
            <section className="store-page-section">
              <SectionTitle overline="A LITTLE SOMETHING TO COME BACK TO" title="Saved pieces." subtitle="Your lovely finds are keeping a place for you." />
              {!wishlist.items.length ? <div className="empty-state">Nothing saved yet. Tap the little heart on anything you love.</div> : <div className="product-grid">{wishlist.items.map(({ product }) => <article className="product-card" key={product.id}><button className="product-image product-tone-2" onClick={() => void openProduct(product.id)}><span>♡</span></button><div className="product-card-info"><div><button className="product-name" onClick={() => void openProduct(product.id)}>{product.name}</button><p>{product.description || "A good thing, saved for later."}</p></div><span>{money(product.price)}</span></div><div className="product-card-actions"><button className="button button-dark" onClick={() => void addToCart(product.id)}>Add to basket</button><button className="small-action danger" onClick={() => void toggleWishlist(product.id)}>Remove</button></div></article>)}</div>}
            </section>
          )}

          {section === "notifications" && (
            <section className="store-page-section">
              <SectionTitle overline="LITTLE UPDATES" title="Your notes." subtitle="Order updates and good-to-know messages live here." />
              <label className="checkbox-row unread-toggle"><input type="checkbox" checked={unreadOnly} onChange={async (event) => { const next = event.target.checked; setUnreadOnly(next); const found = await perform(() => notificationApi.list(next)); if (found) setNotifications(found); }} /> Show unread only</label>
              {process.env.NODE_ENV === "development" && <button className="button button-outline dev-notice-button" onClick={() => void sendTestNotification()}>Send a test note</button>}
              {!notifications.length ? <div className="empty-state">No notes for now. We&apos;ll leave the light on.</div> : <div className="notification-list">{notifications.map((notification) => <article className={`notification-card ${notification.is_read ? "read" : ""}`} key={notification.id}><span className="notification-mark">{notification.is_read ? "○" : "✳"}</span><div><h3>{notification.title}</h3><p>{notification.message}</p><time>{new Date(notification.created_at).toLocaleString()}</time></div>{!notification.is_read && <button className="small-action" onClick={() => void markRead(notification)}>Mark read</button>}</article>)}</div>}
            </section>
          )}

          {section === "products" && isAdmin && (
            <section className="store-page-section">
              <SectionTitle overline="STUDIO / CATALOGUE" title="Your products." subtitle="Create, update, or archive the pieces in your shop." />
              <section className="panel">
                <div className="panel-heading"><div><h2>{editingProduct ? "Edit product" : "Add a product"}</h2><p>Changes are reflected in the public collection.</p></div></div>
                <form className="form-grid" onSubmit={(event) => void submitProduct(event)}>
                  <div className="form-field"><label htmlFor="product-name">Name</label><input id="product-name" required maxLength={255} value={productDraft.name} onChange={(event) => setProductDraft({ ...productDraft, name: event.target.value })} /></div>
                  <div className="form-field"><label htmlFor="product-price">Price</label><input id="product-price" required type="number" min="0" step="0.01" value={productDraft.price} onChange={(event) => setProductDraft({ ...productDraft, price: event.target.value })} /></div>
                  <div className="form-field"><label htmlFor="product-stock">Initial stock</label><input id="product-stock" type="number" min="0" step="1" value={productDraft.stock_quantity} onChange={(event) => setProductDraft({ ...productDraft, stock_quantity: Number(event.target.value) })} /></div>
                  <div className="form-field"><label htmlFor="product-category">Category</label><select id="product-category" value={productDraft.category_id ?? ""} onChange={(event) => setProductDraft({ ...productDraft, category_id: event.target.value ? Number(event.target.value) : null })}><option value="">No category</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></div>
                  <div className="form-field"><label htmlFor="product-image">Image URL</label><input id="product-image" type="url" value={productDraft.image_url ?? ""} onChange={(event) => setProductDraft({ ...productDraft, image_url: event.target.value })} /></div>
                  <div className="form-field form-field-wide"><label htmlFor="product-description">Description</label><textarea id="product-description" value={productDraft.description ?? ""} onChange={(event) => setProductDraft({ ...productDraft, description: event.target.value })} /></div>
                  <div className="form-actions form-field-wide"><button className="button button-dark" disabled={working}>{editingProduct ? "Save product" : "Create product"}</button>{editingProduct && <button type="button" className="button button-plain" onClick={() => {setEditingProduct(null);setProductDraft({name:"",price:"",stock_quantity:0});}}>Cancel</button>}</div>
                </form>
              </section>
              <div className="admin-table">{products.map((product) => <article className="admin-row" key={product.id}><div><strong>{product.name}</strong><span>{money(product.price)} · {product.stock_quantity} in stock</span></div><div className="inline-actions"><button className="small-action" onClick={() => {setEditingProduct(product.id);setProductDraft({name:product.name,price:product.price,stock_quantity:product.stock_quantity,category_id:product.category_id,description:product.description,image_url:product.image_url});}}>Edit</button><button className="small-action danger" onClick={() => void archiveProduct(product)}>Archive</button></div></article>)}</div>
            </section>
          )}

          {section === "inventory" && isAdmin && (
            <section className="store-page-section">
              <SectionTitle overline="STUDIO / STOCKROOM" title="Inventory." subtitle="Check availability and make auditable stock adjustments." />
              <div className="inventory-toolbar"><button className="button button-outline" onClick={async () => {const fresh=await perform(()=>inventoryApi.lowStock());if(fresh)setLowStock(fresh);}}>Refresh low stock</button><span>Showing products at 10 units or fewer.</span></div>
              <div className="admin-table">{lowStock.map((item) => <article className="inventory-summary" key={item.product_id}><span>{item.product_name}</span><strong>{item.stock_quantity} available · low stock</strong></article>)}</div>
              {!lowStock.length && <div className="empty-state">No products are below the low-stock threshold.</div>}
              <div className="inventory-all">
                <h2>All active products</h2>
                {products.map((product) => (
                  <article className="inventory-row" key={product.id}>
                    <div><strong>{product.name}</strong><span>{inventoryChecks[product.id]?.stock_quantity ?? product.stock_quantity} available</span></div>
                    <input aria-label={`Stock adjustment for ${product.name}`} type="number" step="1" placeholder="+ / − units" value={inventoryAdjustments[product.id] ?? ""} onChange={(event) => setInventoryAdjustments({ ...inventoryAdjustments, [product.id]: event.target.value })} />
                    <input aria-label={`Reason for ${product.name}`} placeholder="Reason (optional)" value={inventoryReasons[product.id] ?? ""} onChange={(event) => setInventoryReasons({ ...inventoryReasons, [product.id]: event.target.value })} />
                    <div className="inline-actions">
                      <button className="small-action" onClick={async () => {const checked=await perform(()=>inventoryApi.get(product.id));if(checked)setInventoryChecks({...inventoryChecks,[product.id]:checked});}}>Check stock</button>
                      <button className="button button-dark" onClick={() => void adjustStock(product.id)}>Adjust</button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          {section === "coupons" && isAdmin && (
            <section className="store-page-section">
              <SectionTitle overline="STUDIO / LITTLE EXTRAS" title="Coupons." subtitle="Create a thank-you or update a current offer." />
              <section className="panel">
                <div className="panel-heading"><div><h2>{editingCoupon ? "Update coupon" : "Create a coupon"}</h2><p>Codes can be a percentage or a fixed amount.</p></div></div>
                <form className="form-grid" onSubmit={(event) => void submitCoupon(event)}>
                  {!editingCoupon && <div className="form-field"><label htmlFor="coupon-code">Code</label><input id="coupon-code" required pattern="[A-Za-z0-9_-]+" value={couponDraft.code} onChange={(event) => setCouponDraft({ ...couponDraft, code: event.target.value.toUpperCase() })} /></div>}
                  <div className="form-field"><label htmlFor="coupon-type">Discount type</label><select id="coupon-type" value={couponDraft.discount_type} onChange={(event) => setCouponDraft({ ...couponDraft, discount_type: event.target.value as "percentage" | "fixed" })}><option value="percentage">Percentage</option><option value="fixed">Fixed amount</option></select></div>
                  <div className="form-field"><label htmlFor="coupon-value">{couponDraft.discount_type === "percentage" ? "Percent (1-100)" : "Amount"}</label><input id="coupon-value" required type="number" min="0.01" max={couponDraft.discount_type === "percentage" ? 100 : undefined} step="0.01" value={couponDraft.discount_value} onChange={(event) => setCouponDraft({ ...couponDraft, discount_value: Number(event.target.value) })} /></div>
                  <div className="form-field"><label htmlFor="coupon-minimum">Minimum order amount</label><input id="coupon-minimum" type="number" min="0" step="0.01" value={couponDraft.minimum_order_amount} onChange={(event) => setCouponDraft({ ...couponDraft, minimum_order_amount: Number(event.target.value) })} /></div>
                  <div className="form-field"><label htmlFor="coupon-cap">Maximum discount (optional)</label><input id="coupon-cap" type="number" min="0.01" step="0.01" value={couponDraft.maximum_discount} onChange={(event) => setCouponDraft({ ...couponDraft, maximum_discount: event.target.value })} /></div>
                  <div className="form-field"><label htmlFor="coupon-limit">Usage limit (optional)</label><input id="coupon-limit" type="number" min="1" step="1" value={couponDraft.usage_limit} onChange={(event) => setCouponDraft({ ...couponDraft, usage_limit: event.target.value })} /></div>
                  <div className="form-field"><label htmlFor="coupon-start">Starts at (optional)</label><input id="coupon-start" type="datetime-local" value={couponDraft.starts_at} onChange={(event) => setCouponDraft({ ...couponDraft, starts_at: event.target.value })} /></div>
                  <div className="form-field"><label htmlFor="coupon-expiry">Expires at (optional)</label><input id="coupon-expiry" type="datetime-local" value={couponDraft.expires_at} onChange={(event) => setCouponDraft({ ...couponDraft, expires_at: event.target.value })} /></div>
                  <div className="form-actions form-field-wide"><button className="button button-dark" disabled={working}>{editingCoupon ? "Save coupon" : "Create coupon"}</button>{editingCoupon && <button type="button" className="button button-plain" onClick={() => {setEditingCoupon(null);setCouponDraft({code:"",discount_type:"percentage",discount_value:10,minimum_order_amount:0,maximum_discount:"",usage_limit:"",starts_at:"",expires_at:""});}}>Cancel</button>}</div>
                </form>
              </section>
              <div className="admin-table">{coupons.map((coupon) => <article className="admin-row" key={coupon.id}><div><strong>{coupon.code}</strong><span>{coupon.discount_value}{coupon.discount_type === "percentage" ? "%" : " off"} · used {coupon.usage_count}{coupon.usage_limit ? ` / ${coupon.usage_limit}` : ""}</span></div><span className={`status-pill ${coupon.is_active ? "" : "status-cancelled"}`}>{coupon.is_active ? "active" : "inactive"}</span><div className="inline-actions"><button className="small-action" onClick={() => {setEditingCoupon(coupon.id);setCouponDraft({code:coupon.code,discount_type:coupon.discount_type,discount_value:Number(coupon.discount_value),minimum_order_amount:Number(coupon.minimum_order_amount),maximum_discount:coupon.maximum_discount ?? "",usage_limit:coupon.usage_limit ? String(coupon.usage_limit) : "",starts_at:coupon.starts_at ? new Date(coupon.starts_at).toISOString().slice(0,16) : "",expires_at:coupon.expires_at ? new Date(coupon.expires_at).toISOString().slice(0,16) : ""});}}>Edit</button><button className="small-action" onClick={() => void toggleCoupon(coupon)}>{coupon.is_active ? "Disable" : "Enable"}</button></div></article>)}</div>
            </section>
          )}

          {section === "admin-orders" && isAdmin && (
            <section className="store-page-section">
              <SectionTitle overline="STUDIO / FULFILMENT" title="Manage orders." subtitle="Move orders along and add tracking details." />
              {!adminOrders.length ? <div className="empty-state">No orders are waiting in the studio.</div> : <div className="order-list">{adminOrders.map((order) => <article className="order-card" key={order.id}><div className="order-card-head"><div><span className="store-overline">ORDER NOOK-{order.id} · CUSTOMER {order.user_id}</span><h3>{new Date(order.created_at).toLocaleString()}</h3></div><span className="status-pill">{order.status.replaceAll("_", " ")}</span></div><p>{order.items.map((item) => `${item.product_name} × ${item.quantity}`).join(" · ")}</p><div className="order-card-foot"><strong>{money(order.total)}</strong><div className="inline-actions">{order.status === "paid" && <button className="small-action" onClick={() => void setAdminStatus(order, "processing")}>Start processing</button>}{["paid","processing"].includes(order.status) && <button className="small-action" onClick={() => void setAdminStatus(order, "shipped")}>Mark shipped</button>}{order.status === "shipped" && <button className="small-action" onClick={() => void setAdminStatus(order, "delivered")}>Mark delivered</button>}{["paid","processing","cancellation_requested"].includes(order.status) && <button className="small-action danger" onClick={() => void setAdminStatus(order, "cancelled")}>Cancel order</button>}{order.status === "cancellation_requested" && <button className="small-action" onClick={() => void setAdminStatus(order, "processing")}>Resume</button>}</div></div></article>)}</div>}
            </section>
          )}
        </section>
      </div>
      <footer className="site-footer"><Link className="wordmark" href="/">nook<span>.</span></Link><p>A little more lovely, every day.</p><span>Thoughtfully gathered · ✳</span></footer>
    </main>
  );
}

function SectionTitle({
  overline,
  title,
  subtitle,
}: {
  overline: string;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="store-section-title">
      <p className="eyebrow"><span className="eyebrow-dot" /> {overline}</p>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  );
}
