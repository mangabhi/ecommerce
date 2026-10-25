import ProductDetails from "@/components/product-details";

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const productId = Number(id);

  if (!Number.isInteger(productId) || productId < 1) {
    return (
      <main className="standalone-page">
        <p className="form-error">This product could not be found.</p>
      </main>
    );
  }

  return <ProductDetails productId={productId} />;
}
