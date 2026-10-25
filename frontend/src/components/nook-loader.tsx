export function NookLoader({ label }: { label: string }) {
  return (
    <div className="nook-loader" role="status" aria-label={label}>
      <span className="nook-loader-flower" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
        <b />
      </span>
      <span className="nook-loader-label">{label}</span>
    </div>
  );
}
