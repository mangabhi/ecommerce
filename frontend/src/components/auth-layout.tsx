import Link from "next/link";

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="auth-shell">
      <aside className="auth-aside">
        <Link className="wordmark" href="/" aria-label="Nook home">
          nook<span>.</span>
        </Link>
        <div className="auth-aside-copy">
          <p>A good thing starts with feeling at home.</p>
          <span>Your own little corner, ready when you are.</span>
        </div>
        <div className="auth-aside-footer">Thoughtful things for everyday living · ✳</div>
      </aside>
      <section className="auth-main">
        <div className="auth-card">{children}</div>
      </section>
    </main>
  );
}
