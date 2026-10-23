# Nook storefront frontend

Next.js App Router frontend for the FastAPI service in `../backend`. The
frontend lives independently in this folder; no backend files are changed.

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
- Sign out and revoke the refresh token.

Session tokens are held in `sessionStorage` for the current browser tab. The
backend remains authoritative for authentication, validation, and stored data.

The current backend does not yet expose product, cart, checkout, or order
routes, so this first frontend milestone intentionally focuses on the
implemented authentication and account APIs.

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