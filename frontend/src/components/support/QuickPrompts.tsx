import type { DemoScenario } from "../../types";

interface QuickPromptsProps {
  scenarios: DemoScenario[];
  disabled?: boolean;
  onSelect: (scenario: DemoScenario) => void;
}

export function QuickPrompts({
  scenarios,
  disabled = false,
  onSelect,
}: QuickPromptsProps) {
  return (
    <div>
      <h2 className="text-sm font-black text-slate-900">
        Quick demo scenarios
      </h2>

      <p className="mt-1 text-xs leading-5 text-slate-500">
        Selecting a scenario fills the customer, order and
        message. It does not submit automatically.
      </p>

      <div className="mt-3 space-y-2">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(scenario)}
            className={[
              "w-full rounded-xl border",
              "border-slate-200 bg-white",
              "p-3 text-left shadow-sm",
              "transition",
              "hover:border-blue-300",
              "hover:bg-blue-50",
              "focus-visible:outline-none",
              "focus-visible:ring-2",
              "focus-visible:ring-blue-500",
              "disabled:cursor-not-allowed",
              "disabled:opacity-60",
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-3">
              <span className="text-sm font-bold text-slate-900">
                {scenario.title}
              </span>

              <span
                className={[
                  "shrink-0 rounded-full",
                  "bg-slate-100 px-2 py-1",
                  "text-[10px] font-black",
                  "uppercase tracking-wide",
                  "text-slate-600",
                ].join(" ")}
              >
                {scenario.resultLabel}
              </span>
            </div>

            <span className="mt-1 block text-xs leading-5 text-slate-500">
              {scenario.description}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}