# ResolveAI Refund Policy

**Policy version:** 1.0  
**Effective for:** ResolveAI demonstration environment

## Purpose

This policy defines when an e-commerce refund may be
automatically approved, denied or escalated for human review.

The language model does not have authority to approve refunds.
The enforceable decision is produced by the deterministic Python
policy engine in `backend/app/policy/engine.py`.

---

## Decision types

### APPROVED

The request passed all automatic refund checks.

### DENIED

The request violated a rule that prevents refund processing.

### ESCALATED

The request requires a human decision. No refund is issued
automatically.

---

## Policy rules

### RP-001 — Thirty-day return window

A standard return must be requested no later than 30 calendar
days after delivery.

A request made exactly 30 days after delivery is eligible.

A request made 31 or more days after delivery is denied.

### RP-002 — Delivered order requirement

An order must have a `DELIVERED` status before a standard refund
can be processed.

Orders that are processing, shipped or cancelled are not eligible
for an automatic standard refund.

### RP-003 — Non-refundable products

The following products are non-refundable:

- Final-sale products
- Gift cards
- Downloadable products
- Personalized products

### RP-004 — Opened hygiene products

An opened hygiene-sensitive product is non-refundable.

### RP-005 — Duplicate refund protection

An order that has already been fully refunded cannot be refunded
again.

### RP-006 — Quantity validation

The requested refund quantity cannot exceed the quantity
purchased in the order.

### RP-007 — Standard-return shipping

For a normal change-of-mind return, original shipping charges are
non-refundable.

Only the eligible item amount is refunded.

### RP-008 — Damage, defect or incorrect-item exception

A verified damaged, defective or incorrect product reported no
later than seven calendar days after delivery may receive a full
refund.

The full refund includes:

- Eligible item amount
- Original shipping charge

### RP-009 — High-value human review

A candidate refund amount greater than $500.00 requires human
review.

A candidate refund amount of exactly $500.00 does not require
human review solely because of value.

### RP-010 — Fraud-review account

A customer account marked with a fraud-review flag must be
escalated to a human.

The system does not automatically approve or deny the request.

### RP-011 — Verification requirement

No refund may be processed when any of the following cannot be
verified:

- Customer identity
- Order ownership
- Order ID
- Required order details
- Delivery date when required

The system must not reveal another customer's order information.

### RP-012 — Original payment method

An approved refund must return to the payment method stored on the
original order.

The customer cannot replace the refund destination through chat.

---

## Rule priority

Rules are applied in this order:

1. Identity, ownership and required-data validation
2. Duplicate refund protection
3. Requested quantity validation
4. Fraud-review and high-value escalation
5. Non-refundable product restrictions
6. Delivery status and return-window validation
7. Damage, defect or incorrect-item exception
8. Refund amount calculation
9. Original payment-method enforcement

---

## Policy interpretations

### Return-window boundaries

The 30-day period is inclusive.

- Day 30: eligible
- Day 31: outside the window

The seven-day product-issue period is also inclusive.

- Day 7: eligible for the verified issue exception
- Day 8: not eligible for the exception

### High-value threshold

Only amounts greater than $500.00 are escalated under RP-009.

Exactly $500.00 does not trigger RP-009.

### High-value candidate amount

For a standard return, the candidate amount excludes original
shipping.

For a verified damaged, defective or incorrect item within seven
days, the candidate amount includes original shipping.

### Product restrictions and damaged items

Non-refundable product restrictions are checked before the
damaged-item exception.

A final-sale, gift-card, downloadable or personalized product does
not become automatically refundable merely because a product
issue is claimed.

### Unverified product-issue claims

An unverified damaged, defective or incorrect-item claim does not
receive the seven-day shipping-inclusive exception.

When the product otherwise qualifies for a normal return, the
request may still be evaluated as a standard return with shipping
excluded.

### Partial quantities

The refundable item amount is:

`item price × requested quantity`

For an eligible verified product issue, the original shipping
charge is included once per refund request.

### Customer-data protection

When order ownership fails, the system returns a generic
verification failure.

It does not reveal the name or identity of the actual order owner.

---

## Authority boundary

The language model may:

- Understand the customer message
- Extract a refund reason
- Ask for missing information
- Call tools
- Explain the final decision

The language model may not:

- Override a policy result
- Change the refundable amount
- Approve a denied request
- Automatically approve an escalated request
- Change the original payment method
- Issue a refund without policy approval