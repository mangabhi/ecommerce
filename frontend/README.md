# Nook storefront frontend

Next.js App Router frontend for the FastAPI service in `../backend`. The
frontend lives independently in this folder and calls the backend through its
same-origin API proxy.

## Requirements

- Node.js 20.19 or later
- npm
- The FastAPI backend running at `http://127.0.0.1:8000`

## Run locally (PowerShell)

From this folder:

```powershell
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. Start the API separately from `../backend` using
the backend's own setup instructions. If the API runs somewhere else, update
`BACKEND_API_URL` in `.env.local` and restart the frontend.

The Next.js route handler at `/api/backend/*` forwards requests to the FastAPI
`/api/v1/*` routes, so the browser uses a same-origin URL and does not require a
backend CORS change.

## Connected features

- Create an account and sign in.
- View and update the signed-in user's profile.
- Create, edit, and delete saved addresses.
- Browse products and categories; use the cart, checkout, orders, coupons,
  inventory, reviews, wishlist, and notifications.
- Administer products, stock, coupons, orders, and users from the Studio
  navigation shown to administrator accounts.
- Search and page through users, edit their name, phone, role, and active
  status, or permanently delete customer accounts.
- Open a dedicated product details page, add items to the basket, and check
  out with saved or new delivery details and Stripe Elements.
- View a receipt with purchased items and delivery details after payment.
- Sign out and revoke the refresh token.

Session tokens are held in `sessionStorage` for the current browser tab. The
backend remains authoritative for authentication, validation, and stored data.

## Check the admin changes locally

1. Start the backend from a PowerShell window:

   ```powershell
   Set-Location ..\backend
   .\env\Scripts\Activate.ps1
   $env:APP_ENV = "development"
   python -m scripts.seed_demo_data
   fastapi dev main.py --reload
   ```

   Demo data is inserted into the database configured for the backend and can
   be seeded again safely. Use only a development/test database.

2. Start the frontend in a second PowerShell window:

   ```powershell
   Set-Location frontend
   if (!(Test-Path .env.local)) { Copy-Item .env.example .env.local }
   npm run dev
   ```

   Open `http://localhost:3000` and sign in with the development admin account:
   `demo.admin@example.com` / `DemoPass123!`.

3. In the left-hand **Studio** navigation, open **Manage users**. Search for a
   name or email, edit a user's role or active status, or choose **Delete
   permanently** on a customer and confirm the prompt. Deletion also removes
   data linked to that account, including order and payment history.

4. To check the protected API directly, open `http://127.0.0.1:8000/docs`,
   authorize with an admin access token, and try `GET /api/v1/admin/users`.
   The frontend obtains and sends this token after you sign in.

Do not use the demo credentials outside a development/test environment.

### Configure Stripe test mode

Copy `backend/.env.example` to `backend/.env` if you do not already have a
backend environment file, then set your Stripe test `STRIPE_SECRET_KEY` and
`STRIPE_PUBLISHABLE_KEY`. Never commit real keys or paste secret keys into
source files. Restart the backend after changing environment variables.

To receive payment status updates, install Stripe CLI and run:

```powershell
stripe listen --forward-to http://127.0.0.1:8000/api/v1/payments/webhook/stripe
```

Copy the `whsec_...` signing secret printed by the CLI into
`STRIPE_WEBHOOK_SECRET` in `backend/.env`, then restart the backend.

For test card numbers and scenarios (successful payments, declines, and
authentication challenges), see the official
[Stripe testing documentation](https://docs.stripe.com/testing). A working
Stripe test account and network access are required; without Stripe keys
checkout is intentionally disabled. Local HTTP is supported for test keys;
live Stripe integrations must be served over HTTPS.

## Commands

```powershell
npm run dev
npm run lint
npm run build
```



Kubernetes manages containers running across a cluster.
Component	What it does
Cluster	The complete Kubernetes environment
Node	A machine that runs application workloads
Pod	The smallest deployable unit, usually containing a container
Deployment	Manages Pods, replicas and replacement of failed Pods
Service	Provides a stable network endpoint for accessing Pods

For your application, the relationship will look like this:
- A Deployment manages your FastAPI backend Pods.
- Another Deployment manages your Next.js frontend Pods.
- Services let the frontend and other clients reach the appropriate Pods.
Important: Kubernetes is not a replacement for Docker. Docker builds and packages your images; Kubernetes runs and manages your application workloads.

A Namespace is like a separate workspace inside a Kubernetes cluster. It helps organize and isolate resources.