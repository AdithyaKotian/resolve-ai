import type { AgentEvent } from "../../types";

import { EventDetails } from "./EventDetails";
import { StatusBadge } from "./StatusBadge";

interface ExecutionTimelineProps {
  events: AgentEvent[];
  isLoading: boolean;
}

function eventTone(
  event: AgentEvent,
): "green" | "red" | "amber" | "blue" | "slate" {
  if (
    event.event_type === "RETRY_STARTED"
  ) {
    return "amber";
  }

  if (
    event.execution_status === "FAILED"
  ) {
    return "red";
  }

  if (
    event.execution_status === "RUNNING"
  ) {
    return "blue";
  }

  if (
    event.execution_status === "SUCCEEDED" ||
    event.execution_status === "COMPLETED"
  ) {
    return "green";
  }

  return "slate";
}

function formatTimestamp(
  timestamp: string,
): string {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
    },
  ).format(new Date(timestamp));
}

export function ExecutionTimeline({
  events,
  isLoading,
}: ExecutionTimelineProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <header className="border-b border-slate-200 px-5 py-4">
        <h2 className="font-black text-slate-950">
          Structured execution timeline
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          Safe node, tool and policy events—no private model
          chain-of-thought.
        </p>
      </header>

      {isLoading && events.length === 0 ? (
        <div className="p-8 text-center text-sm text-slate-500">
          Loading execution events...
        </div>
      ) : events.length === 0 ? (
        <div className="p-8 text-center">
          <p className="font-black text-slate-900">
            No execution events
          </p>

          <p className="mt-2 text-sm text-slate-500">
            Select a session that has started processing.
          </p>
        </div>
      ) : (
        <ol className="divide-y divide-slate-100">
          {events.map((event, index) => (
            <li
              key={event.event_id}
              className="relative px-5 py-5"
            >
              <div className="flex gap-4">
                <div className="flex flex-col items-center">
                  <span
                    className={[
                      "flex h-8 w-8",
                      "items-center justify-center",
                      "rounded-full bg-slate-900",
                      "text-xs font-black text-white",
                    ].join(" ")}
                  >
                    {index + 1}
                  </span>

                  {index < events.length - 1 ? (
                    <span className="mt-2 h-full w-px bg-slate-200" />
                  ) : null}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge
                          label={event.event_type}
                          tone={eventTone(event)}
                        />

                        {event.decision ? (
                          <StatusBadge
                            label={event.decision}
                            tone={
                              event.decision ===
                              "APPROVED"
                                ? "green"
                                : event.decision ===
                                    "DENIED"
                                  ? "red"
                                  : "amber"
                            }
                          />
                        ) : null}
                      </div>

                      <p className="mt-3 font-mono text-sm font-black text-slate-900">
                        {event.graph_node ??
                          "Unspecified node"}
                      </p>

                      {event.tool_name ? (
                        <p className="mt-1 text-xs font-semibold text-blue-700">
                          Tool: {event.tool_name}
                        </p>
                      ) : null}
                    </div>

                    <div className="text-left sm:text-right">
                      <p className="text-xs font-bold text-slate-500">
                        {formatTimestamp(
                          event.timestamp,
                        )}
                      </p>

                      <p className="mt-1 text-[11px] text-slate-400">
                        Retry {event.retry_count}
                        {event.latency_ms !== null
                          ? ` · ${event.latency_ms} ms`
                          : ""}
                      </p>
                    </div>
                  </div>

                  {event.matched_policy_rule_codes
                    .length > 0 ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {event.matched_policy_rule_codes.map(
                        (ruleCode) => (
                          <span
                            key={ruleCode}
                            className={[
                              "rounded-md bg-slate-100",
                              "px-2 py-1",
                              "text-[10px] font-black",
                              "text-slate-600",
                            ].join(" ")}
                          >
                            {ruleCode}
                          </span>
                        ),
                      )}
                    </div>
                  ) : null}

                  {event.error_message ? (
                    <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">
                      {event.error_message}
                    </div>
                  ) : null}

                  {event.sanitized_input ||
                  event.tool_output_summary ? (
                    <details className="mt-4 rounded-xl border border-slate-200 bg-slate-50">
                      <summary
                        className={[
                          "cursor-pointer px-4 py-3",
                          "text-xs font-black",
                          "text-slate-700",
                        ].join(" ")}
                      >
                        View sanitized event details
                      </summary>

                      <div className="space-y-4 border-t border-slate-200 p-4">
                        <EventDetails
                          title="Sanitized input"
                          value={
                            event.sanitized_input
                          }
                        />

                        <EventDetails
                          title="Output summary"
                          value={
                            event.tool_output_summary
                          }
                        />
                      </div>
                    </details>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}