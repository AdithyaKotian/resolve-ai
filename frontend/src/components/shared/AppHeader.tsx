import { NavLink } from "react-router";

import { BackendStatus } from "./BackendStatus";

function navigationClass(isActive: boolean): string {
  const baseClasses = [
    "rounded-lg px-3 py-2",
    "text-sm font-semibold",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-blue-500",
    "focus-visible:ring-offset-2",
  ];

  const activeClasses = [
    "bg-slate-900",
    "text-white",
  ];

  const inactiveClasses = [
    "text-slate-600",
    "hover:bg-slate-100",
    "hover:text-slate-950",
  ];

  return [
    ...baseClasses,
    ...(isActive ? activeClasses : inactiveClasses),
  ].join(" ");
}

export function AppHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div
        className={[
          "mx-auto flex max-w-7xl",
          "flex-col gap-4 px-4 py-4",
          "sm:px-6",
          "lg:flex-row lg:items-center lg:justify-between",
          "lg:px-8",
        ].join(" ")}
      >
        <div className="flex items-center justify-between gap-4">
          <NavLink
            to="/"
            className={[
              "flex items-center gap-3",
              "rounded-lg",
              "focus-visible:outline-none",
              "focus-visible:ring-2",
              "focus-visible:ring-blue-500",
              "focus-visible:ring-offset-2",
            ].join(" ")}
          >
            <span
              className={[
                "flex h-10 w-10 items-center justify-center",
                "rounded-xl bg-blue-600",
                "text-sm font-black text-white",
                "shadow-sm",
              ].join(" ")}
              aria-hidden="true"
            >
              R
            </span>

            <span>
              <span className="block text-lg font-black text-slate-950">
                ResolveAI
              </span>

              <span className="block text-xs font-medium text-slate-500">
                Refund Support Agent
              </span>
            </span>
          </NavLink>

          <div className="lg:hidden">
            <BackendStatus />
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <nav
            className="flex items-center gap-1"
            aria-label="Primary navigation"
          >
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                navigationClass(isActive)
              }
            >
              Customer Support
            </NavLink>

            <NavLink
              to="/admin"
              className={({ isActive }) =>
                navigationClass(isActive)
              }
            >
              Admin Dashboard
            </NavLink>
          </nav>

          <div className="hidden lg:block">
            <BackendStatus />
          </div>
        </div>
      </div>
    </header>
  );
}