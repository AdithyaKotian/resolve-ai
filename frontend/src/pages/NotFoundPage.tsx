import { Link } from "react-router";

import { PageShell } from "../components/shared/PageShell";

export function NotFoundPage() {
  return (
    <PageShell>
      <section className="mx-auto max-w-xl rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-12">
        <p className="text-sm font-black uppercase tracking-[0.2em] text-blue-700">
          Error 404
        </p>

        <h1 className="mt-4 text-3xl font-black text-slate-950">
          Page not found
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          The page you requested does not exist in ResolveAI.
        </p>

        <Link
          to="/"
          className={[
            "mt-7 inline-flex rounded-xl",
            "bg-slate-900 px-5 py-3",
            "text-sm font-bold text-white",
            "transition-colors hover:bg-slate-700",
            "focus-visible:outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-blue-500",
            "focus-visible:ring-offset-2",
          ].join(" ")}
        >
          Return to Customer Support
        </Link>
      </section>
    </PageShell>
  );
}