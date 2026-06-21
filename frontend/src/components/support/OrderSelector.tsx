import type { OrderSummary } from "../../types";

interface OrderSelectorProps {
  orders: OrderSummary[];
  selectedOrderId: string;
  isLoading: boolean;
  customerSelected: boolean;
  disabled?: boolean;
  onChange: (orderId: string) => void;
}

function formatMoney(value: string): string {
  const numberValue = Number(value);

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(numberValue);
}

export function OrderSelector({
  orders,
  selectedOrderId,
  isLoading,
  customerSelected,
  disabled = false,
  onChange,
}: OrderSelectorProps) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <label
          htmlFor="order-selector"
          className="text-sm font-bold text-slate-800"
        >
          Order
        </label>

        <span className="text-xs font-medium text-slate-500">
          Optional
        </span>
      </div>

      <select
        id="order-selector"
        value={selectedOrderId}
        disabled={
          !customerSelected ||
          isLoading ||
          disabled
        }
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
          {!customerSelected
            ? "Select a customer first"
            : isLoading
              ? "Loading orders..."
              : "Let the agent ask for the order"}
        </option>

        {orders.map((order) => (
          <option
            key={order.order_id}
            value={order.order_id}
          >
            {order.order_id} — {order.product_name} —{" "}
            {formatMoney(order.total_amount)}
          </option>
        ))}
      </select>
    </div>
  );
}