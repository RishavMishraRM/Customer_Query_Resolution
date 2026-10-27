# DEMO POLICY DOCUMENT - FOR DEMONSTRATION USE ONLY
# SOP Identifier: SOP-UPI-002
# Policy Title: Standard Operating Procedure for Pending UPI Merchant and P2P Transactions

## 1. Scope and Applicability
Applies to Unified Payments Interface (UPI) transactions where the status appears as 'PENDING', 'PROCESSING', or 'DEEMED DECLINED' at the merchant checkout or recipient terminal, while the sender's account reflects a debit.

## 2. Root Causes
- Asynchronous communication between the Remitter Bank, NPCI UPI switch, and Acquiring Merchant Aggregator.
- Session timeout during high-volume merchant processing windows (e.g., peak retail hours, festival sales).
- Delayed response from the Remitter's Mobile Banking App or UPI third-party app provider (TPAP).

## 3. Customer Care Agent Action Items
1. **Explain the Deemed Pending Window:**
   - UPI transactions undergo continuous settlement cycles orchestrated by NPCI.
   - For merchant payments (P2M), explain to the customer that the transaction is in an intermediate state. The merchant aggregator will either accept the funds (completing the order) or reject them within **24 hours**.
2. **Advice Regarding Re-initiating Payment:**
   - If the customer is physically at a store or attempting an urgent bill payment, advise them to wait **15 minutes** before making a duplicate payment, or opt for an alternate payment method (Cash / Card) only after checking that the merchant terminal explicitly reports failure.
   - Reassure the customer that if both transactions succeed, one will be reversed automatically upon settlement audit.
3. **Turnaround Time (TAT) for Reversal:**
   - In case the pending transaction ultimately fails, the amount will be automatically refunded to the customer's bank account within **T+1 business day** (max 48 hours for UPI).

## 4. Prohibited Agent Conduct
- Never request or ask the customer to read out their UPI PIN, OTP, or CVV.
- Never ask the customer to scan any QR code or install remote screen-sharing software (AnyDesk, TeamViewer) to receive a refund.

## 5. Escalation Matrix
- If the status remains 'PENDING' after **48 hours**, escalate to **Digital Payments Resolution Cell (Ticket Queue: UPI-REV-Q2)**.
- For high-priority merchants (utilities, medical emergencies), flag ticket with 'URGENT-ESC-1'.
