import { PageShell } from "../components/shared/PageShell";

const safeguards = [
  {
    title: "Verified customer data",
    description:
      "Customer and order information comes from the seeded CRM database rather than being invented by the model.",
  },
  {
    title: "Deterministic decisions",
    description:
      "Normal Python policy rules remain the final authority for approval, denial and human review.",
  },
  {
    title: "Auditable execution",
    description:
      "Every graph node and backend tool creates a safe structured execution event.",
  },
];

export function CustomerSupportPage() {
  return (
    <PageShell>
      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1.25fr_0.75fr] lg:p-10">
          <div>
            <div
              className={[
                "mb-5 inline-flex rounded-full",
                "border border-blue-200 bg-blue-50",
                "px-3 py-1",
                "text-xs font-bold uppercase",
                "tracking-[0.18em] text-blue-700",
              ].join(" ")}
            >
              AI customer support
            </div>

            <h1
              className={[
                "max-w-3xl text-3xl font-black",
                "tracking-tight text-slate-950",
                "sm:text-4xl lg:text-5xl",
              ].join(" ")}
            >
              Refund support that follows policy—not pressure.
            </h1>

            <p
              className={[
                "mt-5 max-w-2xl",
                "text-base leading-7 text-slate-600",
                "sm:text-lg",
              ].join(" ")}
            >
              ResolveAI verifies the customer and order,
              evaluates deterministic refund rules and
              communicates an approved, denied or escalated
              decision.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white">
            <p className="text-sm font-bold text-blue-300">
              Authority boundary
            </p>

            <p className="mt-3 text-2xl font-black leading-tight">
              The language model understands the request.
            </p>

            <p className="mt-3 text-sm leading-6 text-slate-300">
              The Python policy engine controls the financial
              decision and refundable amount.
            </p>
          </div>
        </div>
      </section>

      <section
        className="mt-8 grid gap-4 md:grid-cols-3"
        aria-label="ResolveAI safeguards"
      >
        {safeguards.map((safeguard) => (
          <article
            key={safeguard.title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h2 className="text-base font-black text-slate-950">
              {safeguard.title}
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              {safeguard.description}
            </p>
          </article>
        ))}
      </section>
    </PageShell>
  );
}