import { apiRequest } from "./client";

import type {
  CustomerOrdersResponse,
  CustomerSummary,
} from "../types";

export function getCustomers(): Promise<CustomerSummary[]> {
  return apiRequest<CustomerSummary[]>("/api/customers");
}

export function getCustomerOrders(
  customerId: string,
): Promise<CustomerOrdersResponse> {
  const encodedCustomerId =
    encodeURIComponent(customerId);

  return apiRequest<CustomerOrdersResponse>(
    `/api/customers/${encodedCustomerId}/orders`,
  );
}