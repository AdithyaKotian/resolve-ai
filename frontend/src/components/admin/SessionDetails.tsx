import type {
  PolicyDecision,
  SessionDetailResponse,
} from "../../types";

import { StatusBadge } from "./StatusBadge";

interface SessionDetailsProps {
  detail: SessionDetailResponse | null;
  isLoading: boolean;
}

function decisionTone(
  decision: PolicyDecision,
): "green" | "red" | "amber" {
  if (decision === "APPROVED") {
    return "green";
  }

  if (decision === "DENIED") {
    return "red";
  }

  return "amber";
}

function formatMoney(
  amount: string,
): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      style: "currency",
      currency: "USD",
    },
  ).format(Number(amount));
}

export function SessionDetails({
  detail,
  isLoading,
}: SessionDetailsProps) {
  if (isLoading && !detail) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-semibold text-slate-500">
          Loading session details...
        </p>
      </section>
    );
  }

  if (!detail) {
    return (
      <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="font-black text-slate-900">
          Select an agent session
        </p>

        <p className="mt-2 text-sm text-slate-500">
          Session details and conversation history will appear
          here.
        </p>
      </section>
    );
  }

  const { session, messages, decision_result } =
    detail;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <header className="border-b border-slate-200 p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-wide text-slate-500">
              Selected session
            </p>

            <h2
              className="mt-2 truncate font-mono text-sm font-black text-slate-950"
              title={session.session_id}
            >
              {session.session_id}
            </h2>
          </div>

          <div className="flex flex-wrap gap-2">
            <StatusBadge
              label={session.status}
              tone={
                session.status === "COMPLETED"
                  ? "green"
                  : session.status === "FAILED"
                    ? "red"
                    : "blue"
              }
            />

            {session.final_decision ? (
              <StatusBadge
                label={session.final_decision}
                tone={decisionTone(
                  session.final_decision,
                )}
              />
            ) : null}
          </div>
        </div>

        <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
          <div className="rounded-xl bg-slate-50 p-3">
            <dt className="text-xs font-bold text-slate-500">
              Customer
            </dt>

            <dd className="mt-1 font-mono text-xs font-black text-slate-900">
              {session.customer_id ?? "Not resolved"}
            </dd>
          </div>

          <div className="rounded-xl bg-slate-50 p-3">
            <dt className="text-xs font-bold text-slate-500">
              Order
            </dt>

            <dd className="mt-1 font-mono text-xs font-black text-slate-900">
              {session.order_id ?? "Not resolved"}
            </dd>
          </div>
        </dl>
      </header>

      {decision_result ? (
        <div className="border-b border-slate-200 p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-black uppercase tracking-wide text-slate-500">
                Final policy decision
              </p>

              <div className="mt-2">
                <StatusBadge
                  label={
                    decision_result.decision
                  }
                  tone={decisionTone(
                    decision_result.decision,
                  )}
                />
              </div>
            </div>

            <div className="sm:text-right">
              <p className="text-xs font-bold text-slate-500">
                Refundable amount
              </p>

              <p className="mt-1 text-2xl font-black text-slate-950">
                {formatMoney(
                  decision_result.refundable_amount,
                )}
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {decision_result.rule_codes.map(
              (ruleCode) => (
                <span
                  key={ruleCode}
                  className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-600"
                >
                  {ruleCode}
                </span>
              ),
            )}
          </div>

          {decision_result.refund_reference ? (
            <p className="mt-4 break-all font-mono text-xs font-bold text-emerald-700">
              Refund reference:{" "}
              {decision_result.refund_reference}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="p-5">
        <h3 className="font-black text-slate-950">
          Conversation
        </h3>

        <div className="mt-4 max-h-72 space-y-3 overflow-auto">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-500">
              No conversation messages stored.
            </p>
          ) : (
            messages.map((message) => (
              <article
                key={message.message_id}
                className={[
                  "rounded-xl p-3",
                  message.role === "user"
                    ? "ml-8 bg-blue-50"
                    : "mr-8 bg-slate-100",
                ].join(" ")}
              >
                <p className="text-[10px] font-black uppercase tracking-wide text-slate-500">
                  {message.role === "user"
                    ? "Customer"
                    : "ResolveAI"}
                </p>

                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                  {message.content}
                </p>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
}