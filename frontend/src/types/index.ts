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
export interface AgentEvent {
  event_id: number;
  session_id: string;
  timestamp: string;

  event_type: string;
  graph_node: string | null;
  tool_name: string | null;

  sanitized_input: Record<string, unknown> | null;
  tool_output_summary:
    | Record<string, unknown>
    | null;

  matched_policy_rule_codes: string[];

  decision: PolicyDecision | null;
  execution_status: string;

  latency_ms: number | null;
  retry_count: number;
  error_message: string | null;
}

export interface StoredChatMessage {
  message_id: number;
  session_id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface SessionSummary {
  session_id: string;

  customer_id: string | null;
  order_id: string | null;

  status: SessionStatus;
  final_decision: PolicyDecision | null;

  created_at: string;
  updated_at: string;

  event_count: number;
  tool_failures: number;
}

export interface SessionMetrics {
  total_sessions: number;
  approved_refunds: number;
  denied_refunds: number;
  escalated_requests: number;
  tool_failures: number;
}

export interface SessionListResponse {
  metrics: SessionMetrics;
  sessions: SessionSummary[];
}

export interface SessionDetailResponse {
  session: SessionSummary;
  messages: StoredChatMessage[];
  decision_result: DecisionResult | null;
}

export type WebSocketConnectionStatus =
  | "connected"
  | "disconnected";