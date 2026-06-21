import type { SessionMetrics } from "../../types";

interface SummaryCardsProps {
  metrics: SessionMetrics;
}

interface SummaryCard {
  label: string;
  value: number;
  description: string;
  containerClass: string;
  valueClass: string;
}

export function SummaryCards({
  metrics,
}: SummaryCardsProps) {
  const cards: SummaryCard[] = [
    {
      label: "Total sessions",
      value: metrics.total_sessions,
      description:
        "All customer refund conversations",
      containerClass:
        "border-slate-200 bg-white",
      valueClass: "text-slate-950",
    },
    {
      label: "Approved",
      value: metrics.approved_refunds,
      description:
        "Refunds automatically executed",
      containerClass:
        "border-emerald-200 bg-emerald-50",
      valueClass: "text-emerald-700",
    },
    {
      label: "Denied",
      value: metrics.denied_refunds,
      description:
        "Requests blocked by policy",
      containerClass:
        "border-red-200 bg-red-50",
      valueClass: "text-red-700",
    },
    {
      label: "Human review",
      value: metrics.escalated_requests,
      description:
        "Requests requiring manual review",
      containerClass:
        "border-amber-200 bg-amber-50",
      valueClass: "text-amber-700",
    },
    {
      label: "Tool failures",
      value: metrics.tool_failures,
      description:
        "Controlled backend tool errors",
      containerClass:
        "border-blue-200 bg-blue-50",
      valueClass: "text-blue-700",
    },
  ];

  return (
    <section
      className={[
        "grid gap-4",
        "sm:grid-cols-2",
        "xl:grid-cols-5",
      ].join(" ")}
      aria-label="Agent session summary"
    >
      {cards.map((card) => (
        <article
          key={card.label}
          className={[
            "rounded-2xl border p-5",
            "shadow-sm",
            card.containerClass,
          ].join(" ")}
        >
          <p
            className={[
              "text-3xl font-black",
              card.valueClass,
            ].join(" ")}
          >
            {card.value}
          </p>

          <h2 className="mt-2 text-sm font-black text-slate-900">
            {card.label}
          </h2>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            {card.description}
          </p>
        </article>
      ))}
    </section>
  );
}