export type MembershipTier =
  | "STANDARD"
  | "SILVER"
  | "GOLD"
  | "PLATINUM";

export type OrderStatus =
  | "PROCESSING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED";

export type ProductCondition =
  | "UNOPENED"
  | "OPENED"
  | "DAMAGED"
  | "DEFECTIVE"
  | "INCORRECT_ITEM";

export type RefundStatus =
  | "NONE"
  | "PENDING"
  | "PARTIAL"
  | "FULL"
  | "DENIED"
  | "HUMAN_REVIEW";

export type PolicyDecision =
  | "APPROVED"
  | "DENIED"
  | "ESCALATED";

export type SessionStatus =
  | "ACTIVE"
  | "COMPLETED"
  | "FAILED";

export interface BackendHealth {
  status: "ok";
  app_name: string;
  version: string;
  environment: string;
  database: "connected";
  timestamp: string;
}

export interface CustomerSummary {
  customer_id: string;
  full_name: string;
  email: string;
  membership_tier: MembershipTier;
  fraud_review_flag: boolean;
  total_orders: number;
  previous_refunds: number;
}

export interface OrderSummary {
  order_id: string;
  customer_id: string;

  product_name: string;
  product_category: string;
  quantity: number;

  item_price: string;
  shipping_amount: string;
  total_amount: string;

  order_date: string;
  delivery_date: string | null;

  order_status: OrderStatus;
  product_condition: ProductCondition;
  refund_status: RefundStatus;

  final_sale: boolean;
  personalized: boolean;
  downloadable: boolean;
  hygiene_sensitive: boolean;

  payment_method: string;
}

export interface CustomerOrdersResponse {
  customer: CustomerSummary;
  orders: OrderSummary[];
}

export interface ChatRequest {
  session_id?: string;
  customer_id: string;
  order_id?: string;
  message: string;
  simulate_transient_failure?: boolean;
}

export interface DecisionResult {
  decision: PolicyDecision;
  order_id: string;

  refundable_amount: string;
  rule_codes: string[];
  reasons: string[];

  refund_reference: string | null;
  human_review_case_id: string | null;
  payment_method: string | null;
}

export interface ChatResponse {
  session_id: string;
  session_status: SessionStatus;
  assistant_message: string;
  decision_result: DecisionResult | null;
  retry_count: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  customerId: string;
  orderId: string;
  message: string;
  resultLabel: string;
}