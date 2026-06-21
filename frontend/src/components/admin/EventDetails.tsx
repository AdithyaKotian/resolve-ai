interface EventDetailsProps {
  title: string;
  value: Record<string, unknown> | null;
}

export function EventDetails({
  title,
  value,
}: EventDetailsProps) {
  if (!value) {
    return null;
  }

  return (
    <div>
      <p className="text-[11px] font-black uppercase tracking-wide text-slate-500">
        {title}
      </p>

      <pre
        className={[
          "mt-2 max-h-64 overflow-auto",
          "rounded-xl bg-slate-950",
          "p-4 text-xs leading-5",
          "text-slate-200",
        ].join(" ")}
      >
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}