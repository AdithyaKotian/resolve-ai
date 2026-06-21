import { PageShell } from "../components/shared/PageShell";
import { LoadingSpinner } from "../components/shared/LoadingSpinner";

import { ExecutionTimeline } from "../components/admin/ExecutionTimeline";
import { SessionDetails } from "../components/admin/SessionDetails";
import { SessionsTable } from "../components/admin/SessionsTable";
import { StatusBadge } from "../components/admin/StatusBadge";
import { SummaryCards } from "../components/admin/SummaryCards";

import { useAdminDashboard } from "../hooks/useAdminDashboard";

function formatUpdatedTime(
  timestamp: string | null,
): string {
  if (!timestamp) {
    return "Not updated yet";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
    },
  ).format(new Date(timestamp));
}

export function AdminDashboardPage() {
  const {
    dashboard,

    selectedSessionId,
    selectedSession,
    events,

    isLoadingSessions,
    isLoadingDetails,

    webSocketStatus,

    error,
    lastUpdated,

    selectSession,
    refreshDashboard,
  } = useAdminDashboard();

  return (
    <PageShell>
      <section className="flex flex-col gap-5 border-b border-slate-200 pb-7 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.18em] text-blue-700">
            Operational visibility
          </p>

          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
            Agent Admin Dashboard
          </h1>

          <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
            Inspect customer sessions, tool execution,
            deterministic policy results and controlled retry
            behaviour in real time.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge
            label={
              webSocketStatus === "connected"
                ? "Live connection"
                : "Live connection offline"
            }
            tone={
              webSocketStatus === "connected"
                ? "green"
                : "red"
            }
          />

          <button
            type="button"
            disabled={isLoadingSessions}
            onClick={() => {
              void refreshDashboard();
            }}
            className={[
              "inline-flex min-w-28",
              "items-center justify-center",
              "rounded-xl border",
              "border-slate-300 bg-white",
              "px-4 py-2.5",
              "text-sm font-black",
              "text-slate-700",
              "shadow-sm transition",
              "hover:bg-slate-50",
              "focus-visible:outline-none",
              "focus-visible:ring-2",
              "focus-visible:ring-blue-500",
              "disabled:cursor-not-allowed",
              "disabled:opacity-60",
            ].join(" ")}
          >
            {isLoadingSessions ? (
              <LoadingSpinner
                label="Refreshing"
                size="small"
              />
            ) : (
              "Refresh"
            )}
          </button>
        </div>
      </section>

      {error ? (
        <div
          className={[
            "mt-6 rounded-xl border",
            "border-red-200 bg-red-50",
            "px-4 py-3",
            "text-sm font-semibold text-red-700",
          ].join(" ")}
          role="alert"
        >
          {error}
        </div>
      ) : null}

      <div className="mt-3 text-right text-xs font-medium text-slate-400">
        Last updated:{" "}
        {formatUpdatedTime(lastUpdated)}
      </div>

      <div className="mt-5">
        <SummaryCards
          metrics={dashboard.metrics}
        />
      </div>

      <div className="mt-6">
        <SessionsTable
          sessions={dashboard.sessions}
          selectedSessionId={
            selectedSessionId
          }
          isLoading={isLoadingSessions}
          onSelect={selectSession}
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[390px_minmax(0,1fr)]">
        <SessionDetails
          detail={selectedSession}
          isLoading={isLoadingDetails}
        />

        <ExecutionTimeline
          events={events}
          isLoading={isLoadingDetails}
        />
      </div>
    </PageShell>
  );
}