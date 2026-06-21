import type { CustomerSummary } from "../../types";

interface CustomerSelectorProps {
  customers: CustomerSummary[];
  selectedCustomerId: string;
  isLoading: boolean;
  disabled?: boolean;
  onChange: (customerId: string) => void;
}

export function CustomerSelector({
  customers,
  selectedCustomerId,
  isLoading,
  disabled = false,
  onChange,
}: CustomerSelectorProps) {
  return (
    <div>
      <label
        htmlFor="customer-selector"
        className="text-sm font-bold text-slate-800"
      >
        Demo customer
      </label>

      <select
        id="customer-selector"
        value={selectedCustomerId}
        disabled={isLoading || disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className={[
          "mt-2 w-full rounded-xl border",
          "border-slate-300 bg-white",
          "px-3 py-3 text-sm text-slate-900",
          "shadow-sm outline-none",
          "transition",
          "focus:border-blue-500",
          "focus:ring-4 focus:ring-blue-100",
          "disabled:cursor-not-allowed",
          "disabled:bg-slate-100",
          "disabled:text-slate-500",
        ].join(" ")}
      >
        <option value="">
          {isLoading
            ? "Loading customers..."
            : "Select a customer"}
        </option>

        {customers.map((customer) => (
          <option
            key={customer.customer_id}
            value={customer.customer_id}
          >
            {customer.full_name} — {customer.customer_id}
          </option>
        ))}
      </select>
    </div>
  );
}