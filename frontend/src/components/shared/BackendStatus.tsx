import { useEffect, useState } from "react";

import { getBackendHealth } from "../../api/health";

type ConnectionStatus = "checking" | "online" | "offline";

export function BackendStatus() {
  const [status, setStatus] =
    useState<ConnectionStatus>("checking");

  useEffect(() => {
    let componentIsMounted = true;

    async function checkBackend(): Promise<void> {
      try {
        await getBackendHealth();

        if (componentIsMounted) {
          setStatus("online");
        }
      } catch {
        if (componentIsMounted) {
          setStatus("offline");
        }
      }
    }

    void checkBackend();

    return () => {
      componentIsMounted = false;
    };
  }, []);

  const statusConfig = {
    checking: {
      label: "Checking backend",
      dotClass: "bg-amber-400",
      textClass: "text-amber-700",
      containerClass:
        "border-amber-200 bg-amber-50",
    },

    online: {
      label: "Backend online",
      dotClass: "bg-emerald-500",
      textClass: "text-emerald-700",
      containerClass:
        "border-emerald-200 bg-emerald-50",
    },

    offline: {
      label: "Backend offline",
      dotClass: "bg-red-500",
      textClass: "text-red-700",
      containerClass: "border-red-200 bg-red-50",
    },
  } satisfies Record<
    ConnectionStatus,
    {
      label: string;
      dotClass: string;
      textClass: string;
      containerClass: string;
    }
  >;

  const currentStatus = statusConfig[status];

  return (
    <div
      className={[
        "inline-flex items-center gap-2 rounded-full",
        "border px-3 py-1.5 text-xs font-semibold",
        currentStatus.containerClass,
        currentStatus.textClass,
      ].join(" ")}
      role="status"
      aria-live="polite"
    >
      <span
        className={[
          "h-2 w-2 rounded-full",
          currentStatus.dotClass,
        ].join(" ")}
        aria-hidden="true"
      />

      {currentStatus.label}
    </div>
  );
}