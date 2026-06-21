type BadgeTone =
  | "green"
  | "red"
  | "amber"
  | "blue"
  | "slate";

interface StatusBadgeProps {
  label: string;
  tone?: BadgeTone;
}

const toneClasses: Record<
  BadgeTone,
  string
> = {
  green:
    "border-emerald-200 bg-emerald-50 text-emerald-700",

  red:
    "border-red-200 bg-red-50 text-red-700",

  amber:
    "border-amber-200 bg-amber-50 text-amber-700",

  blue:
    "border-blue-200 bg-blue-50 text-blue-700",

  slate:
    "border-slate-200 bg-slate-100 text-slate-600",
};

export function StatusBadge({
  label,
  tone = "slate",
}: StatusBadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full",
        "border px-2.5 py-1",
        "text-[10px] font-black uppercase",
        "tracking-wide",
        toneClasses[tone],
      ].join(" ")}
    >
      {label.replaceAll("_", " ")}
    </span>
  );
}