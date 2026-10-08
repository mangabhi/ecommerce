"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiError, authApi } from "@/lib/api";
import { AuthLayout } from "@/components/auth-layout";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await authApi.register({
        email,
        full_name: fullName,
        phone: phone || null,
        password,
      });
      router.push("/login");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "We couldn't create your account. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <Link className="back-home" href="/">← <span>Back to nook</span></Link>
      <p className="eyebrow"><span className="eyebrow-dot" /> MAKE YOURSELF AT HOME</p>
      <h1 className="auth-title">A place for you.</h1>
      <p className="auth-subtitle">
        Create your account and get your little corner ready.
      </p>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-field form-field-wide">
            <label htmlFor="full-name">Your name</label>
            <input
              id="full-name"
              name="full_name"
              autoComplete="name"
              minLength={2}
              maxLength={255}
              placeholder="How should we call you?"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              required
            />
          </div>
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
            <label htmlFor="phone">Phone <span>(optional)</span></label>
            <input
              id="phone"
              name="phone"
              type="tel"
              autoComplete="tel"
              maxLength={20}
              placeholder="+1 555 000 0000"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
            />
          </div>
          <div className="form-field form-field-wide">
            <label htmlFor="password">Create a password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
              placeholder="At least 8 characters"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="button button-dark auth-submit" disabled={submitting}>
          {submitting ? "Creating your account…" : "Create your account"}
          <span aria-hidden="true">↗</span>
        </button>
      </form>
      <p className="auth-switch">
        Already have an account? <Link href="/login">Sign in</Link>
      </p>
    </AuthLayout>
  );
}
