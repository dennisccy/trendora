export function PageHeading({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="space-y-1">
      <h1 className="text-lg font-semibold tracking-tight text-text">{title}</h1>
      {subtitle ? <p className="text-sm text-text-muted">{subtitle}</p> : null}
    </div>
  );
}
