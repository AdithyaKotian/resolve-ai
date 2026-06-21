import { LoadingSpinner } from "../shared/LoadingSpinner";

interface DemoControlsProps {
  simulateTransientFailure: boolean;
  isSending: boolean;
  isResetting: boolean;

  onSimulationChange: (
    enabled: boolean,
  ) => void;

  onReset: () => Promise<void>;
}

export function DemoControls({
  simulateTransientFailure,
  isSending,
  isResetting,
  onSimulationChange,
  onReset,
}: DemoControlsProps) {
  const controlsDisabled =
    isSending || isResetting;

  function handleReset(): void {
    const confirmed = window.confirm(
      "Reset all demo sessions, events and refund activity? " +
        "The original 15 customers and 22 orders will be restored.",
    );

    if (confirmed) {
      void onReset();
    }
  }

  return (
    <div>
      <h2 className="text-sm font-black text-slate-900">
        Demo controls
      </h2>

      <p className="mt-1 text-xs leading-5 text-slate-500">
        Use these controls to demonstrate retry handling and
        restore the original database state before recording.
      </p>

      <label
        className={[
          "mt-4 flex cursor-pointer",
          "items-start gap-3 rounded-xl",
          "border border-slate-200",
          "bg-slate-50 p-3",
        ].join(" ")}
      >
        <input
          type="checkbox"
          checked={simulateTransientFailure}
          disabled={controlsDisabled}
          onChange={(event) =>
            onSimulationChange(
              event.target.checked,
            )
          }
          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
        />

        <span>
          <span className="block text-sm font-black text-slate-800">
            Simulate one transient CRM failure
          </span>

          <span className="mt-1 block text-xs leading-5 text-slate-500">
            The first customer lookup fails, the graph retries
            once and then continues normally.
          </span>
        </span>
      </label>

      <button
        type="button"
        disabled={controlsDisabled}
        onClick={handleReset}
        className={[
          "mt-4 inline-flex w-full",
          "items-center justify-center",
          "rounded-xl border",
          "border-red-200 bg-red-50",
          "px-4 py-2.5",
          "text-sm font-black text-red-700",
          "transition hover:bg-red-100",
          "focus-visible:outline-none",
          "focus-visible:ring-2",
          "focus-visible:ring-red-500",
          "disabled:cursor-not-allowed",
          "disabled:opacity-50",
        ].join(" ")}
      >
        {isResetting ? (
          <LoadingSpinner
            label="Resetting demo"
            size="small"
          />
        ) : (
          "Reset demo environment"
        )}
      </button>
    </div>
  );
}