export type Session = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type UserProfile = {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  phone: string | null;
  date_of_birth: string | null;
  avatar_url: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type Address = {
  id: number;
  user_id: number;
  label: string;
  recipient_name: string;
  phone: string | null;
  address_line1: string;
  address_line2: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type AddressInput = Omit<
  Address,
  "id" | "user_id" | "created_at" | "updated_at"
>;

export type ProfileInput = Partial<
  Pick<UserProfile, "full_name" | "phone" | "date_of_birth" | "avatar_url">
>;

export type Product = {
  id: number;
  category_id: number | null;
  name: string;
  description: string | null;
  price: string;
  stock_quantity: number;
  image_url: string | null;
  created_at: string;
  updated_at: string;
};

export type ProductInput = {
  category_id?: number | null;
  name: string;
  description?: string | null;
  price: number | string;
  stock_quantity?: number;
  image_url?: string | null;
};

export type Category = {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type CartItem = {
  id: number;
  product_id: number;
  quantity: number;
  product: Product;
  subtotal: string;
};

export type Cart = {
  id: number;
  user_id: number;
  items: CartItem[];
  subtotal: string;
  created_at: string;
  updated_at: string;
};

export type Inventory = {
  product_id: number;
  product_name: string;
  stock_quantity: number;
};

export type InventoryAdjustment = {
  id: number;
  product_id: number;
  adjusted_by: number | null;
  change: number;
  stock_after: number;
  reason: string | null;
  created_at: string;
};

export type OrderItem = {
  id: number;
  product_id: number | null;
  product_name: string;
  unit_price: string;
  quantity: number;
};

export type Order = {
  id: number;
  user_id: number;
  status: string;
  subtotal: string;
  discount_amount: string;
  total: string;
  coupon_code: string | null;
  shipping_address: Record<string, string | null>;
  tracking_number: string | null;
  tracking_status: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
};

export type Coupon = {
  id: number;
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: string;
  minimum_order_amount: string;
  maximum_discount: string | null;
  usage_limit: number | null;
  usage_count: number;
  starts_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CouponQuote = {
  subtotal: string;
  discount_amount: string;
  total: string;
  coupon_code: string | null;
};

export type Payment = {
  id: number;
  order_id: number;
  user_id: number;
  provider: string;
  provider_reference: string;
  status: string;
  amount: string;
  currency: string;
  refund_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type Review = {
  id: number;
  product_id: number;
  user_id: number;
  reviewer_name: string;
  rating: number;
  title: string | null;
  body: string | null;
  created_at: string;
  updated_at: string;
};

export type Wishlist = {
  items: { id: number; product_id: number; product: Product; created_at: string }[];
};

export type Notification = {
  id: number;
  user_id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
};

type SessionResponse = Omit<Session, "refresh_token"> & {
  refresh_token?: string;
};

const SESSION_KEY = "ecommerce-session";
let refreshInFlight: Promise<boolean> | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function saveSession(session: Session) {
  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession() {
  window.sessionStorage.removeItem(SESSION_KEY);
}

export function hasSession() {
  return window.sessionStorage.getItem(SESSION_KEY) !== null;
}

function getSession(): Session | null {
  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    clearSession();
    return null;
  }
}

async function readResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  const payload: unknown = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : payload;
    const message = Array.isArray(detail)
      ? detail
          .map((item) =>
            typeof item === "object" && item !== null && "msg" in item
              ? String((item as { msg: unknown }).msg)
              : "Invalid input",
          )
          .join(", ")
      : typeof detail === "string"
        ? detail
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }
  return payload as T;
}

async function send<T>(
  path: string,
  init: RequestInit,
  accessToken?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  return readResponse<T>(
    await fetch(`/api/backend${path}`, { ...init, headers, cache: "no-store" }),
  );
}

async function refreshSession(): Promise<boolean> {
  const session = getSession();
  if (!session) return false;
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const refreshed = await send<SessionResponse>(
          "/auth/refresh",
          {
            method: "POST",
            body: JSON.stringify({ refresh_token: session.refresh_token }),
          },
        );
        saveSession({
          ...session,
          access_token: refreshed.access_token,
          token_type: refreshed.token_type,
        });
        return true;
      } catch {
        clearSession();
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const current = getSession();
  try {
    return await send<T>(path, init, current?.access_token);
  } catch (cause) {
    if (
      !(cause instanceof ApiError) ||
      cause.status !== 401 ||
      !current ||
      path === "/auth/refresh" ||
      path === "/auth/logout"
    ) {
      throw cause;
    }
    if (!(await refreshSession())) throw cause;
    const refreshed = getSession();
    if (!refreshed) throw cause;
    return send<T>(path, init, refreshed.access_token);
  }
}

function queryString(values: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && value !== "") query.set(key, String(value));
  }
  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
}

export const authApi = {
  async login(email: string, password: string) {
    const session = await apiFetch<Session>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    saveSession(session);
    return session;
  },
  register: (input: {
    email: string;
    full_name: string;
    phone: string | null;
    password: string;
  }) =>
    apiFetch<{ id: number; email: string; full_name: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  refresh: refreshSession,
  async logout() {
    const session = getSession();
    if (!session) return;
    try {
      await apiFetch<{ message: string }>("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: session.refresh_token }),
      });
    } finally {
      clearSession();
    }
  },
};

export const userApi = {
  getProfile: () => apiFetch<UserProfile>("/users/me"),
  updateProfile: (input: ProfileInput) =>
    apiFetch<UserProfile>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
  getAddresses: () => apiFetch<Address[]>("/users/me/addresses"),
  createAddress: (input: AddressInput) =>
    apiFetch<Address>("/users/me/addresses", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  updateAddress: (id: number, input: Partial<AddressInput>) =>
    apiFetch<Address>(`/users/me/addresses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
  deleteAddress: (id: number) =>
    apiFetch<void>(`/users/me/addresses/${id}`, { method: "DELETE" }),
};

export const productApi = {
  list: (filters: {
    search?: string;
    min_price?: string;
    max_price?: string;
    sort_by?: "name" | "price" | "created_at";
    order?: "asc" | "desc";
    limit?: number;
    offset?: number;
  } = {}) => apiFetch<Product[]>(`/products${queryString(filters)}`),
  get: (id: number) => apiFetch<Product>(`/products/${id}`),
  create: (input: ProductInput) =>
    apiFetch<Product>("/products", { method: "POST", body: JSON.stringify(input) }),
  update: (id: number, input: Partial<ProductInput>) =>
    apiFetch<Product>(`/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
  archive: (id: number) => apiFetch<void>(`/products/${id}`, { method: "DELETE" }),
};

export const categoryApi = {
  list: () => apiFetch<Category[]>("/categories"),
  products: (id: number) => apiFetch<Product[]>(`/categories/${id}/products`),
};

export const cartApi = {
  get: () => apiFetch<Cart>("/cart"),
  add: (product_id: number, quantity: number) =>
    apiFetch<Cart>("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id, quantity }),
    }),
  update: (item_id: number, quantity: number) =>
    apiFetch<Cart>(`/cart/items/${item_id}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),
  remove: (item_id: number) =>
    apiFetch<Cart>(`/cart/items/${item_id}`, { method: "DELETE" }),
  clear: () => apiFetch<void>("/cart", { method: "DELETE" }),
};

export const inventoryApi = {
  get: (productId: number) => apiFetch<Inventory>(`/inventory/${productId}`),
  adjust: (productId: number, change: number, reason: string | null) =>
    apiFetch<InventoryAdjustment>(`/inventory/${productId}`, {
      method: "PATCH",
      body: JSON.stringify({ change, reason }),
    }),
  lowStock: (threshold = 10, limit = 100) =>
    apiFetch<Inventory[]>(`/inventory/low-stock${queryString({ threshold, limit })}`),
};

export const couponApi = {
  validate: (code: string, subtotal: number | string) =>
    apiFetch<CouponQuote>("/coupons/validate", {
      method: "POST",
      body: JSON.stringify({ code, subtotal }),
    }),
  quote: (code: string | null) =>
    apiFetch<CouponQuote>("/checkout/quote", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),
  list: () => apiFetch<Coupon[]>("/admin/coupons"),
  create: (input: {
    code: string;
    discount_type: "percentage" | "fixed";
    discount_value: number;
    minimum_order_amount?: number;
    maximum_discount?: number | null;
    usage_limit?: number | null;
    starts_at?: string | null;
    expires_at?: string | null;
  }) =>
    apiFetch<Coupon>("/admin/coupons", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  update: (
    id: number,
    input: {
      discount_type?: "percentage" | "fixed";
      discount_value?: number;
      minimum_order_amount?: number;
      maximum_discount?: number | null;
      usage_limit?: number | null;
      starts_at?: string | null;
      expires_at?: string | null;
      is_active?: boolean;
    },
  ) =>
    apiFetch<Coupon>(`/admin/coupons/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
};

export const orderApi = {
  checkout: (address_id: number, coupon_code: string | null) =>
    apiFetch<Order>("/checkout", {
      method: "POST",
      body: JSON.stringify({ address_id, coupon_code }),
    }),
  create: (address_id: number, coupon_code: string | null) =>
    apiFetch<Order>("/orders", {
      method: "POST",
      body: JSON.stringify({ address_id, coupon_code }),
    }),
  list: () => apiFetch<Order[]>("/orders"),
  get: (id: number) => apiFetch<Order>(`/orders/${id}`),
  cancel: (id: number, reason: string | null) =>
    apiFetch<Order>(`/orders/${id}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  tracking: (id: number) =>
    apiFetch<{
      order_id: number;
      status: string;
      tracking_number: string | null;
      tracking_status: string | null;
      updated_at: string;
    }>(`/orders/${id}/tracking`),
  adminList: (limit = 50, offset = 0) =>
    apiFetch<Order[]>(`/admin/orders${queryString({ limit, offset })}`),
  adminUpdate: (
    id: number,
    input: {
      status: "processing" | "shipped" | "delivered" | "cancelled";
      tracking_number?: string | null;
      tracking_status?: string | null;
    },
  ) =>
    apiFetch<Order>(`/admin/orders/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
};

export const paymentApi = {
  create: (order_id: number, currency = "USD") =>
    apiFetch<Payment>("/payments/create", {
      method: "POST",
      body: JSON.stringify({ order_id, currency }),
    }),
  get: (id: number) => apiFetch<Payment>(`/payments/${id}`),
  webhook: (input: {
    provider_reference: string;
    status: "succeeded" | "failed";
    amount: string;
  }) =>
    apiFetch<Payment>("/payments/webhook", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  refund: (id: number, reason: string | null) =>
    apiFetch<Payment>(`/payments/${id}/refund`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
};

export const reviewApi = {
  list: (productId: number) =>
    apiFetch<Review[]>(`/products/${productId}/reviews`),
  create: (productId: number, input: { rating: number; title?: string; body?: string }) =>
    apiFetch<Review>(`/products/${productId}/reviews`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  update: (
    id: number,
    input: { rating?: number; title?: string | null; body?: string | null },
  ) =>
    apiFetch<Review>(`/reviews/${id}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
  remove: (id: number) => apiFetch<void>(`/reviews/${id}`, { method: "DELETE" }),
};

export const wishlistApi = {
  get: () => apiFetch<Wishlist>("/wishlist"),
  add: (product_id: number) =>
    apiFetch<Wishlist>("/wishlist/items", {
      method: "POST",
      body: JSON.stringify({ product_id }),
    }),
  remove: (product_id: number) =>
    apiFetch<void>(`/wishlist/items/${product_id}`, { method: "DELETE" }),
};

export const notificationApi = {
  list: (unread_only = false, limit = 50, offset = 0) =>
    apiFetch<Notification[]>(
      `/notifications${queryString({ unread_only: unread_only ? "true" : "false", limit, offset })}`,
    ),
  markRead: (id: number) =>
    apiFetch<Notification>(`/notifications/${id}/read`, { method: "PATCH" }),
  createTest: (title: string, message: string) =>
    apiFetch<Notification>("/notifications/test", {
      method: "POST",
      body: JSON.stringify({ title, message }),
    }),
};
