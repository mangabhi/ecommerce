"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiError, authApi } from "@/lib/api";
import { AuthLayout } from "@/components/auth-layout";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await authApi.login(email, password);
      router.push("/");
      router.refresh();
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "We couldn't sign you in. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <Link className="back-home" href="/">← <span>Back to nook</span></Link>
      <p className="eyebrow"><span className="eyebrow-dot" /> WELCOME BACK</p>
      <h1 className="auth-title">Come on in.</h1>
      <p className="auth-subtitle">
        Sign in to pick up right where you left off.
      </p>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-field form-field-wide">
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <div className="form-field form-field-wide">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="Your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="button button-dark auth-submit" disabled={submitting}>
          {submitting ? "Signing you in…" : "Sign in"} <span aria-hidden="true">↗</span>
        </button>
      </form>
      <p className="auth-switch">
        New around here? <Link href="/register">Create an account</Link>
      </p>
    </AuthLayout>
  );
}
