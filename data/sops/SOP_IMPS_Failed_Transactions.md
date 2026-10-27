# DEMO POLICY DOCUMENT - FOR DEMONSTRATION USE ONLY
# SOP Identifier: SOP-IMPS-001
# Policy Title: Standard Operating Procedure for Failed IMPS Transactions

## 1. Overview and Scope
This standard operating procedure governs customer inquiries regarding Immediate Payment Service (IMPS) transactions where the sender's account has been debited but the beneficiary has not received the funds, or where the transaction status is marked as 'FAILED'.

## 2. Technical Causes of IMPS Failures
IMPS failures commonly occur due to:
- Beneficiary bank core banking system (CBS) timeout or switch downtime (Error code M4/M5).
- NPCI (National Payments Corporation of India) clearing house switch failure.
- Incorrect beneficiary IFSC code or invalid account number provided by the sender.

## 3. Standard Resolution Workflow for Call Center Agents
1. **Verification of Transaction ID:** Prompt the customer to confirm the last 4 digits of the transaction reference number (RRN/Txn ID) and the registered account number.
2. **Debit & Settlement Status Check:** 
   - Check the CBS core switch log.
   - If the switch response is 'DEEMED REVERSED' or 'FAILED', the funds are placed in the bank's internal suspense pooling account.
3. **Turnaround Time (TAT) Communication:**
   - Inform the customer that as per standard automated reconciliation cycles, the debited amount will be automatically reversed to their source account within **T+1 working day** (where T is the date of transaction).
   - If the funds are not credited back within T+1 working days, a formal grievance ticket must be raised for manual reconciliation.
4. **Compensation Guidelines:**
   - Under demo guidelines, if credit reversal exceeds T+1 days due to remitter bank delay, standard statutory compensation of ₹100 per day of delay applies subject to bank verification.

## 4. Agent Scripting Instructions
- Reassure the customer that their money is safe in the banking reconciliation channel.
- Never promise immediate instant refunds while on call; clarify that automated settlement batches run every 6 hours.
- Provide the customer with the internal tracking reference number for their call.

## 5. Escalation Criteria
- If the customer transaction has exceeded **T+2 working days** without reversal, immediately escalate to **Tier-2 Operations Desk (Desk Code: OPS-IMPS-ESC)**.
- If the debited amount exceeds ₹50,000 and status remains indeterminate, log a priority ticket with the Nodal Grievance Officer.
