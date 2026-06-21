interface LoadingSpinnerProps {
  label?: string;
  size?: "small" | "medium";
}

export function LoadingSpinner({
  label = "Loading",
  size = "medium",
}: LoadingSpinnerProps) {
  const spinnerSize =
    size === "small" ? "h-4 w-4" : "h-5 w-5";

  return (
    <span
      className="inline-flex items-center gap-2"
      role="status"
      aria-live="polite"
    >
      <span
        className={[
          spinnerSize,
          "animate-spin rounded-full",
          "border-2 border-current",
          "border-r-transparent",
        ].join(" ")}
        aria-hidden="true"
      />

      <span>{label}</span>
    </span>
  );
}