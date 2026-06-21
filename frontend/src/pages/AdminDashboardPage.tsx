import { PageShell } from "../components/shared/PageShell";

const dashboardSections = [
  {
    title: "Session overview",
    description:
      "Review the number of approved, denied and escalated refund requests.",
  },
  {
    title: "Execution timeline",
    description:
      "Inspect graph nodes, tool calls, policy rules, retries and execution status.",
  },
  {
    title: "Safe trace details",
    description:
      "View sanitized tool input and output without exposing hidden model reasoning.",
  },
];

export function AdminDashboardPage() {
  return (
    <PageShell>
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-7">
        <p className="text-sm font-bold uppercase tracking-[0.16em] text-blue-700">
          Operational visibility
        </p>

        <h1 className="text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
          Admin Dashboard
        </h1>

        <p className="max-w-3xl text-base leading-7 text-slate-600">
          Inspect the agent’s safe structured execution trace,
          including tool calls, deterministic policy results and
          controlled retries.
        </p>
      </div>

      <section
        className="mt-8 grid gap-4 md:grid-cols-3"
        aria-label="Dashboard capabilities"
      >
        {dashboardSections.map((section) => (
          <article
            key={section.title}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <div
              className={[
                "mb-5 flex h-10 w-10",
                "items-center justify-center",
                "rounded-xl bg-slate-100",
                "text-sm font-black text-slate-700",
              ].join(" ")}
              aria-hidden="true"
            >
              {section.title.charAt(0)}
            </div>

            <h2 className="font-black text-slate-950">
              {section.title}
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              {section.description}
            </p>
          </article>
        ))}
      </section>

      <section className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-8">
        <h2 className="text-lg font-black text-slate-950">
          Backend APIs are ready
        </h2>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Session metrics, stored execution events and WebSocket
          updates will be connected to this interface when the
          dashboard components are built.
        </p>
      </section>
    </PageShell>
  );
}