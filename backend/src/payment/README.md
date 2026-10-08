Base path: /api/v1/payments
Method	Endpoint	Purpose
POST	/payments/create	Initiate payment with a provider
GET	/payments/{payment_id}	Check payment status
POST	/payments/webhook	Receive provider payment events
POST	/payments/{payment_id}/refund	Initiate a refund (authorized users)

Payment creation, status checks, and refunds require an access token. A payment
is created for an order owned by the caller; its amount is taken from that
order, not from client input. In this MVP, payment creation uses a local mock
provider and returns a `provider_reference`. Successful mock payments update
the order to `paid`; failed mock payments release reserved stock.

The mock webhook is disabled unless `APP_ENV=development` and
`MOCK_PAYMENT_WEBHOOK_SECRET` are configured. Send that secret in the
`X-Mock-Webhook-Secret` header and a body such as:

```json
{
  "provider_reference": "returned-by-payment-create",
  "status": "succeeded",
  "amount": 25.00
}
```

The webhook only accepts `succeeded` or `failed`, verifies the amount, and is
idempotent for repeated events with the same result. A user can refund their
own successful payment; admins can refund any successful payment. Mock refunds
complete immediately. This provider is for development and is not a production
payment integration.