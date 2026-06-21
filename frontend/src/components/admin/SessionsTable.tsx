import type {
  PolicyDecision,
  SessionStatus,
  SessionSummary,
} from "../../types";

import { LoadingSpinner } from "../shared/LoadingSpinner";
import { StatusBadge } from "./StatusBadge";

interface SessionsTableProps {
  sessions: SessionSummary[];
  selectedSessionId: string | null;
  isLoading: boolean;
  onSelect: (sessionId: string) => void;
}

function statusTone(
  status: SessionStatus,
): "green" | "red" | "blue" {
  if (status === "COMPLETED") {
    return "green";
  }

  if (status === "FAILED") {
    return "red";
  }

  return "blue";
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

function formatDate(
  timestamp: string,
): string {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    },
  ).format(new Date(timestamp));
}

export function SessionsTable({
  sessions,
  selectedSessionId,
  isLoading,
  onSelect,
}: SessionsTableProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <header className="border-b border-slate-200 px-5 py-4">
        <h2 className="font-black text-slate-950">
          Recent agent sessions
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          Select a session to inspect its complete execution.
        </p>
      </header>

      {isLoading && sessions.length === 0 ? (
        <div className="flex min-h-52 items-center justify-center text-sm text-slate-500">
          <LoadingSpinner
            label="Loading sessions"
            size="small"
          />
        </div>
      ) : sessions.length === 0 ? (
        <div className="min-h-52 p-8 text-center">
          <p className="font-black text-slate-900">
            No agent sessions yet
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Start a conversation from the Customer Support
            page and it will appear here.
          </p>
        </div>
      ) : (
        <div className="max-h-[500px] overflow-auto">
          <table className="w-full min-w-[760px] text-left">
            <thead className="sticky top-0 bg-slate-50">
              <tr className="border-b border-slate-200">
                <th className="px-4 py-3 text-xs font-black uppercase tracking-wide text-slate-500">
                  Session
                </th>

                <th className="px-4 py-3 text-xs font-black uppercase tracking-wide text-slate-500">
                  Customer / Order
                </th>

                <th className="px-4 py-3 text-xs font-black uppercase tracking-wide text-slate-500">
                  Status
                </th>

                <th className="px-4 py-3 text-xs font-black uppercase tracking-wide text-slate-500">
                  Decision
                </th>

                <th className="px-4 py-3 text-xs font-black uppercase tracking-wide text-slate-500">
                  Events
                </th>

                <th className="px-4 py-3 text-xs font-black uppercase tracking-wide text-slate-500">
                  Updated
                </th>
              </tr>
            </thead>

            <tbody>
              {sessions.map((session) => {
                const selected =
                  session.session_id ===
                  selectedSessionId;

                return (
                  <tr
                    key={session.session_id}
                    className={[
                      "border-b border-slate-100",
                      selected
                        ? "bg-blue-50"
                        : "hover:bg-slate-50",
                    ].join(" ")}
                  >
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() =>
                          onSelect(
                            session.session_id,
                          )
                        }
                        className={[
                          "max-w-48 truncate",
                          "font-mono text-xs",
                          "font-black text-blue-700",
                          "hover:underline",
                          "focus-visible:outline-none",
                          "focus-visible:ring-2",
                          "focus-visible:ring-blue-500",
                        ].join(" ")}
                        title={session.session_id}
                      >
                        {session.session_id}
                      </button>
                    </td>

                    <td className="px-4 py-3">
                      <p className="font-mono text-xs font-bold text-slate-700">
                        {session.customer_id ??
                          "Unknown customer"}
                      </p>

                      <p className="mt-1 font-mono text-[11px] text-slate-400">
                        {session.order_id ??
                          "Order not selected"}
                      </p>
                    </td>

                    <td className="px-4 py-3">
                      <StatusBadge
                        label={session.status}
                        tone={statusTone(
                          session.status,
                        )}
                      />
                    </td>

                    <td className="px-4 py-3">
                      {session.final_decision ? (
                        <StatusBadge
                          label={
                            session.final_decision
                          }
                          tone={decisionTone(
                            session.final_decision,
                          )}
                        />
                      ) : (
                        <span className="text-xs font-medium text-slate-400">
                          Pending
                        </span>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      <p className="text-sm font-black text-slate-900">
                        {session.event_count}
                      </p>

                      {session.tool_failures > 0 ? (
                        <p className="mt-1 text-xs font-bold text-red-600">
                          {session.tool_failures} failed
                        </p>
                      ) : null}
                    </td>

                    <td className="px-4 py-3 text-xs font-medium text-slate-500">
                      {formatDate(
                        session.updated_at,
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}