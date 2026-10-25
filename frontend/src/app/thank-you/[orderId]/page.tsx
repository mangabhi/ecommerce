import ThankYouReceipt from "@/components/thank-you-receipt";

export default async function ThankYouPage({
  params,
}: {
  params: Promise<{ orderId: string }>;
}) {
  const { orderId } = await params;
  const parsedOrderId = Number(orderId);

  if (!Number.isInteger(parsedOrderId) || parsedOrderId < 1) {
    return (
      <main className="standalone-page">
        <p className="form-error">We couldn&apos;t find that order.</p>
      </main>
    );
  }

  return <ThankYouReceipt orderId={parsedOrderId} />;
}
