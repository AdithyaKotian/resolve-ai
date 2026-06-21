import type {
  DecisionResult,
  PolicyDecision,
} from "../../types";

interface DecisionCardProps {
  result: DecisionResult;
  retryCount: number;
}

interface DecisionStyle {
  label: string;
  container: string;
  badge: string;
  amountLabel: string;
}

function decisionStyle(
  decision: PolicyDecision,
): DecisionStyle {
  if (decision === "APPROVED") {
    return {
      label: "Refund approved",
      container:
        "border-emerald-200 bg-emerald-50",
      badge:
        "bg-emerald-600 text-white",
      amountLabel: "Approved refund",
    };
  }

  if (decision === "DENIED") {
    return {
      label: "Refund denied",
      container: "border-red-200 bg-red-50",
      badge: "bg-red-600 text-white",
      amountLabel: "Refund amount",
    };
  }

  return {
    label: "Human review required",
    container: "border-amber-200 bg-amber-50",
    badge: "bg-amber-500 text-slate-950",
    amountLabel: "Candidate amount",
  };
}

function formatMoney(value: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value));
}

export function DecisionCard({
  result,
  retryCount,
}: DecisionCardProps) {
  const style = decisionStyle(result.decision);

  return (
    <section
      className={[
        "rounded-2xl border p-5",
        style.container,
      ].join(" ")}
      aria-labelledby="decision-heading"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <span
            className={[
              "inline-flex rounded-full",
              "px-3 py-1",
              "text-xs font-black uppercase",
              "tracking-wide",
              style.badge,
            ].join(" ")}
          >
            {style.label}
          </span>

          <h2
            id="decision-heading"
            className="mt-3 text-xl font-black text-slate-950"
          >
            Order {result.order_id}
          </h2>
        </div>

        <div className="sm:text-right">
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
            {style.amountLabel}
          </p>

          <p className="mt-1 text-2xl font-black text-slate-950">
            {formatMoney(result.refundable_amount)}
          </p>
        </div>
      </div>

      <div className="mt-5">
        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
          Policy rules
        </p>

        <div className="mt-2 flex flex-wrap gap-2">
          {result.rule_codes.map((ruleCode) => (
            <span
              key={ruleCode}
              className={[
                "rounded-lg border",
                "border-slate-300 bg-white",
                "px-2.5 py-1",
                "text-xs font-black text-slate-700",
              ].join(" ")}
            >
              {ruleCode}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-5">
        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
          Explanation
        </p>

        <ul className="mt-2 space-y-2">
          {result.reasons.map((reason) => (
            <li
              key={reason}
              className="flex gap-2 text-sm leading-6 text-slate-700"
            >
              <span
                className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-500"
                aria-hidden="true"
              />

              {reason}
            </li>
          ))}
        </ul>
      </div>

      {result.payment_method ? (
        <div className="mt-5 rounded-xl border border-white/80 bg-white/70 p-3">
          <p className="text-xs font-bold text-slate-500">
            Original payment method
          </p>

          <p className="mt-1 text-sm font-black text-slate-800">
            {result.payment_method}
          </p>
        </div>
      ) : null}

      {result.refund_reference ? (
        <div className="mt-3 rounded-xl border border-emerald-200 bg-white p-3">
          <p className="text-xs font-bold text-emerald-700">
            Refund reference
          </p>

          <p className="mt-1 break-all font-mono text-sm font-black text-slate-900">
            {result.refund_reference}
          </p>
        </div>
      ) : null}

      {result.human_review_case_id ? (
        <div className="mt-3 rounded-xl border border-amber-200 bg-white p-3">
          <p className="text-xs font-bold text-amber-700">
            Human-review case
          </p>

          <p className="mt-1 break-all font-mono text-sm font-black text-slate-900">
            {result.human_review_case_id}
          </p>
        </div>
      ) : null}

      {retryCount > 0 ? (
        <p className="mt-4 text-xs font-bold text-amber-800">
          The workflow recovered after {retryCount} controlled{" "}
          {retryCount === 1 ? "retry" : "retries"}.
        </p>
      ) : null}
    </section>
  );
}