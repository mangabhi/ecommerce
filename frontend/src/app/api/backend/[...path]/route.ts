import type { NextRequest } from "next/server";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyRequest(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const backendOrigin = (
    process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const target = new URL(
    `/api/v1/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
    backendOrigin,
  );
  const headers = new Headers();
  const authorization = request.headers.get("authorization");
  const contentType = request.headers.get("content-type");
  if (authorization) headers.set("Authorization", authorization);
  if (contentType) headers.set("Content-Type", contentType);
  if (
    process.env.APP_ENV === "development" &&
    path.join("/") === "payments/webhook" &&
    process.env.MOCK_PAYMENT_WEBHOOK_SECRET
  ) {
    headers.set(
      "X-Mock-Webhook-Secret",
      process.env.MOCK_PAYMENT_WEBHOOK_SECRET,
    );
  }

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method)
        ? undefined
        : await request.arrayBuffer(),
      cache: "no-store",
    });
    const responseHeaders = new Headers();
    const upstreamContentType = upstream.headers.get("content-type");
    if (upstreamContentType) {
      responseHeaders.set("Content-Type", upstreamContentType);
    }

    return new Response(
      upstream.status === 204 ? null : await upstream.text(),
      {
        status: upstream.status,
        headers: responseHeaders,
      },
    );
  } catch (error) {
    console.error("Backend API proxy request failed:", error);
    return Response.json(
      { detail: "The backend API could not be reached. Check that it is running." },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
