"use client";

import { useState } from "react";
import {
  aiApi,
  type RecommendedProduct,
  type ChatMessage,
} from "@/lib/api";

export default function ShoppingAssistant() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [products, setProducts] = useState<RecommendedProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!message.trim() || loading) return;

    setLoading(true);
    setError("");
    setReply("");
    setProducts([]);

    try {
      const userMessage = message.trim();
      const response = await aiApi.shoppingAssistant(userMessage,history);
      setReply(response.message);
      setProducts(response.products);
      setHistory((previous) => [
      ...previous,
      { role: "user", content: userMessage },
      { role: "assistant", content: response.message },
      ]);
      setMessage("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto w-full max-w-3xl rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-2xl font-semibold text-gray-900">
        AI Shopping Assistant
      </h2>

      <p className="mt-2 text-sm text-gray-600">
        Tell me what you&apos;re looking for, including your budget or preferences.
      </p>

      <form onSubmit={handleSubmit} className="mt-5 flex gap-2">
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="e.g. Find me sneakers under 100"
          maxLength={1000}
          disabled={loading}
          className="min-w-0 flex-1 rounded-lg border border-gray-300 px-4 py-3 text-gray-900 outline-none focus:border-blue-500"
        />

        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Searching..." : "Ask AI"}
        </button>
      </form>

      {error && (
        <p className="mt-4 text-sm text-red-600">{error}</p>
      )}

      {reply && (
        <div className="mt-6">
          <p className="font-medium text-gray-900">{reply}</p>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {products.map((product) => (
              <article
                key={product.id}
                className="overflow-hidden rounded-lg border border-gray-200"
              >
                {product.image_url && (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="h-48 w-full object-cover"
                  />
                )}

                <div className="p-4">
                  <h3 className="font-semibold text-gray-900">
                    {product.name}
                  </h3>

                  <p className="mt-1 text-sm text-gray-600">
                    {product.category_name}
                  </p>

                  <p className="mt-2 font-semibold text-gray-900">
                    ${product.price}
                  </p>

                  <p className="mt-2 text-sm text-gray-600">
                    {product.reason}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}