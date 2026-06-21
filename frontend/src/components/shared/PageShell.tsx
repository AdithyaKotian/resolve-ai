import type { PropsWithChildren } from "react";

import { AppHeader } from "./AppHeader";

export function PageShell({
  children,
}: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-slate-50">
      <AppHeader />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}