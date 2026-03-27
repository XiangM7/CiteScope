type StatusBadgeProps = {
  status: string;
};

const palette: Record<string, string> = {
  uploaded: "bg-amber-100 text-amber-900",
  parsed: "bg-sky-100 text-sky-900",
  indexed: "bg-emerald-100 text-emerald-900",
  failed: "bg-rose-100 text-rose-900"
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${palette[status] ?? "bg-slate-200 text-slate-900"}`}>
      {status}
    </span>
  );
}
