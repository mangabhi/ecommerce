# Payments API

Base path: `/api/v1/payments`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/payments/config` | Return Stripe configuration status and the publishable key |
| POST | `/payments/create` | Create or reuse a Stripe PaymentIntent for the signed-in user's order |
| POST | `/payments/{payment_id}/confirm` | Verify a completed payment directly with Stripe |
| POST | `/payments/webhook/stripe` | Receive signed Stripe payment events |
| GET | `/payments/{payment_id}` | Check payment status |
| POST | `/payments/{payment_id}/refund` | Request a refund (authorized users) |

Payment creation and confirmation require an access token. A PaymentIntent is
created for an order owned by the caller; its amount is taken from the server's
order record, not from client input. Orders awaiting payment reserve inventory
until payment succeeds, fails, or the order is cancelled.

## Stripe setup

Set `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, and
`STRIPE_WEBHOOK_SECRET` in the backend environment. Use Stripe test-mode keys
for local development. `GET /payments/config` exposes only the publishable key.
The browser uses Stripe Elements; card data is sent directly to Stripe and is
never stored by this service. On successful confirmation, the payment record
stores Stripe's PaymentMethod ID for reconciliation; it does not store card
numbers, CVCs, or expiration dates.

HTTP is allowed for local development with Stripe test keys. A live Stripe.js
integration must be served over HTTPS.

Register a webhook endpoint at
`https://<your-api-host>/api/v1/payments/webhook/stripe` for
`payment_intent.succeeded` and `payment_intent.payment_failed`. For local
development, Stripe CLI can forward events to
`http://127.0.0.1:8000/api/v1/payments/webhook/stripe`; use the CLI-provided
`whsec_...` value as `STRIPE_WEBHOOK_SECRET`. Webhook signatures, amount, and
currency are verified before an order is marked paid or inventory is released.
The client confirmation endpoint independently retrieves the PaymentIntent
from Stripe before finalizing a successful payment, so the thank-you receipt
does not depend on webhook delivery timing.

For test card numbers and payment scenarios, see the official
[Stripe testing documentation](https://docs.stripe.com/testing).

Refund requests for Stripe payments are sent to Stripe and use an idempotency
key to avoid duplicate refunds when a request is retried.

The legacy mock webhook is disabled unless `APP_ENV=development` and
`MOCK_PAYMENT_WEBHOOK_SECRET` are configured. It is retained for existing
development integrations and does not create Stripe payments.
