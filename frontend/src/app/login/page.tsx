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
  const [showPassword, setShowPassword] = useState(false);
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
            <div className="password-input-wrap">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              <button
                className="password-visibility-toggle"
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6Z" />
                  <circle cx="12" cy="12" r="2.6" />
                  {showPassword && <path d="m4 4 16 16" />}
                </svg>
              </button>
            </div>
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
