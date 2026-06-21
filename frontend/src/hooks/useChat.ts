import {
  useEffect,
  useRef,
  useState,
} from "react";

import { ApiError } from "../api/client";
import { sendChatMessage } from "../api/chat";
import {
  getCustomerOrders,
  getCustomers,
} from "../api/customers";

import type {
  ChatMessage,
  CustomerSummary,
  DecisionResult,
  DemoScenario,
  OrderSummary,
} from "../types";

interface UseChatResult {
  customers: CustomerSummary[];
  orders: OrderSummary[];

  selectedCustomerId: string;
  selectedOrderId: string;

  messages: ChatMessage[];
  input: string;

  decisionResult: DecisionResult | null;
  retryCount: number;
  sessionId: string | null;

  isLoadingCustomers: boolean;
  isLoadingOrders: boolean;
  isSending: boolean;

  error: string | null;

  setInput: (value: string) => void;
  selectCustomer: (customerId: string) => void;
  selectOrder: (orderId: string) => void;
  applyDemoScenario: (
    scenario: DemoScenario,
  ) => void;
  sendMessage: () => Promise<void>;
  clearConversation: () => void;
}

function createMessage(
  role: ChatMessage["role"],
  content: string,
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "The request could not be completed.";
}

export function useChat(): UseChatResult {
  const [customers, setCustomers] = useState<
    CustomerSummary[]
  >([]);

  const [orders, setOrders] = useState<
    OrderSummary[]
  >([]);

  const [
    selectedCustomerId,
    setSelectedCustomerId,
  ] = useState("");

  const [
    selectedOrderId,
    setSelectedOrderId,
  ] = useState("");

  const [messages, setMessages] = useState<
    ChatMessage[]
  >([]);

  const [input, setInput] = useState("");

  const [sessionId, setSessionId] = useState<
    string | null
  >(null);

  const [
    decisionResult,
    setDecisionResult,
  ] = useState<DecisionResult | null>(null);

  const [retryCount, setRetryCount] = useState(0);

  const [
    isLoadingCustomers,
    setIsLoadingCustomers,
  ] = useState(true);

  const [
    isLoadingOrders,
    setIsLoadingOrders,
  ] = useState(false);

  const [isSending, setIsSending] =
    useState(false);

  const [error, setError] = useState<
    string | null
  >(null);

  const pendingDemoOrderId =
    useRef<string | null>(null);

  function resetConversationState(): void {
    setMessages([]);
    setSessionId(null);
    setDecisionResult(null);
    setRetryCount(0);
    setError(null);
  }

  useEffect(() => {
    let effectIsActive = true;

    async function loadCustomers(): Promise<void> {
      try {
        const customerResults =
          await getCustomers();

        if (!effectIsActive) {
          return;
        }

        setCustomers(customerResults);

        const preferredCustomer =
          customerResults.find(
            (customer) =>
              customer.customer_id ===
              "CUST-VALID-001",
          ) ?? customerResults[0];

        if (preferredCustomer) {
          setIsLoadingOrders(true);

          setSelectedCustomerId(
            preferredCustomer.customer_id,
          );
        }
      } catch (loadError) {
        if (effectIsActive) {
          setError(
            getErrorMessage(loadError),
          );
        }
      } finally {
        if (effectIsActive) {
          setIsLoadingCustomers(false);
        }
      }
    }

    void loadCustomers();

    return () => {
      effectIsActive = false;
    };
  }, []);

  useEffect(() => {
    let effectIsActive = true;

    if (!selectedCustomerId) {
      return () => {
        effectIsActive = false;
      };
    }

    async function loadOrders(): Promise<void> {
      try {
        const result = await getCustomerOrders(
          selectedCustomerId,
        );

        if (!effectIsActive) {
          return;
        }

        setOrders(result.orders);

        const requestedDemoOrder =
          pendingDemoOrderId.current;

        if (
          requestedDemoOrder &&
          result.orders.some(
            (order) =>
              order.order_id ===
              requestedDemoOrder,
          )
        ) {
          setSelectedOrderId(
            requestedDemoOrder,
          );

          pendingDemoOrderId.current = null;
          return;
        }

        setSelectedOrderId(
          (currentOrderId) =>
            result.orders.some(
              (order) =>
                order.order_id ===
                currentOrderId,
            )
              ? currentOrderId
              : "",
        );
      } catch (loadError) {
        if (effectIsActive) {
          setOrders([]);
          setSelectedOrderId("");

          setError(
            getErrorMessage(loadError),
          );
        }
      } finally {
        if (effectIsActive) {
          setIsLoadingOrders(false);
        }
      }
    }

    void loadOrders();

    return () => {
      effectIsActive = false;
    };
  }, [selectedCustomerId]);

  function selectCustomer(
    customerId: string,
  ): void {
    pendingDemoOrderId.current = null;

    setSelectedCustomerId(customerId);
    setOrders([]);
    setSelectedOrderId("");
    setIsLoadingOrders(Boolean(customerId));
    setInput("");

    resetConversationState();
  }

  function selectOrder(orderId: string): void {
    setSelectedOrderId(orderId);
    setInput("");

    resetConversationState();
  }

  function applyDemoScenario(
    scenario: DemoScenario,
  ): void {
    resetConversationState();

    const customerIsChanging =
      selectedCustomerId !==
      scenario.customerId;

    if (customerIsChanging) {
      pendingDemoOrderId.current =
        scenario.orderId;

      setOrders([]);
      setSelectedOrderId("");
      setIsLoadingOrders(true);
    } else {
      pendingDemoOrderId.current = null;

      setSelectedOrderId(
        scenario.orderId,
      );
    }

    setSelectedCustomerId(
      scenario.customerId,
    );

    setInput(scenario.message);
  }

  async function sendMessage(): Promise<void> {
    const cleanedMessage = input.trim();

    if (!selectedCustomerId) {
      setError(
        "Select a demo customer before sending a message.",
      );

      return;
    }

    if (!cleanedMessage || isSending) {
      return;
    }

    const customerMessage = createMessage(
      "user",
      cleanedMessage,
    );

    setMessages((currentMessages) => [
      ...currentMessages,
      customerMessage,
    ]);

    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        session_id:
          sessionId ?? undefined,

        customer_id:
          selectedCustomerId,

        order_id:
          selectedOrderId || undefined,

        message:
          cleanedMessage,
      });

      setSessionId(response.session_id);
      setRetryCount(response.retry_count);

      setDecisionResult(
        response.decision_result,
      );

      setMessages((currentMessages) => [
        ...currentMessages,

        createMessage(
          "assistant",
          response.assistant_message,
        ),
      ]);
    } catch (sendError) {
      setError(
        getErrorMessage(sendError),
      );
    } finally {
      setIsSending(false);
    }
  }

  function clearConversation(): void {
    resetConversationState();
    setInput("");
  }

  return {
    customers,
    orders,

    selectedCustomerId,
    selectedOrderId,

    messages,
    input,

    decisionResult,
    retryCount,
    sessionId,

    isLoadingCustomers,
    isLoadingOrders,
    isSending,

    error,

    setInput,
    selectCustomer,
    selectOrder,
    applyDemoScenario,
    sendMessage,
    clearConversation,
  };
}