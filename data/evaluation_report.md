# FinTech Copilot - Benchmark Evaluation Report

**Date & Time:** 2026-10-25 01:17:06  
**Total Test Cases:** 4  
**Total Evaluation Time:** 116.63s  
**Average Case Latency:** 29.16s  

---

## 1. Summary of Benchmark Results

| Test Case ID | Expected Policy | Retrieval Match | Grounding Keywords | Escalation Match | Confidence | Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `CASE-1-IMPS-FAILED` | `SOP-IMPS-001` | **PASS** | WARN | **PASS** | 0.80 | 30.36s |
| `CASE-2-UPI-PENDING` | `SOP-UPI-002` | **PASS** | WARN | **PASS** | 0.80 | 29.81s |
| `CASE-3-CARD-DISPUTE` | `SOP-CARD-003` | **PASS** | PASS | **PASS** | 0.80 | 27.31s |
| `CASE-4-UNSUPPORTED-OUT-OF-SCOPE` | `None` | **FAIL** | PASS | **WARN** | 0.79 | 29.15s |

---

## 2. Detailed Case Diagnostics

### Case: CASE-1-IMPS-FAILED
- **Input Query:** "Hello, my name is Araf Sharma. My imps transaction of 15,000 rupees failed yesterday evening, but the money was deducted from my account. When will I get my refund back?"
- **Retrieved Policies:** SOP-IMPS-001, SOP-UPI-002
- **Confidence Score:** 0.8
- **Escalation Triggered:** `False` (No escalation)
- **Proposed Agent Script:**
  > "We are reviewing your transaction details in our system. Let me check the latest status."
- **Safety Warnings:** None (Clean)

### Case: CASE-2-UPI-PENDING
- **Input Query:** "Hi, I am pre-inair. I tried to pay 3450 rupees at FreshMart grocery store via UPI, but the merchant scanner showed payment pending while my account was debited. What should I do now?"
- **Retrieved Policies:** SOP-IMPS-001, SOP-UPI-002
- **Confidence Score:** 0.8
- **Escalation Triggered:** `False` (No escalation)
- **Proposed Agent Script:**
  > "We are reviewing your transaction details in our system. Let me check the latest status."
- **Safety Warnings:** None (Clean)

### Case: CASE-3-CARD-DISPUTE
- **Input Query:** "Good afternoon, this is Vikram Mulhotra. I noticed an 8,999 rupees charge posted twice on my credit card statement for Aero Electronics Store. I only swiped once. Please dispute this second charge."
- **Retrieved Policies:** SOP-CARD-003, SOP-IMPS-001
- **Confidence Score:** 0.8
- **Escalation Triggered:** `False` (No escalation)
- **Proposed Agent Script:**
  > "Good afternoon, Vikram. We understand your concern about the duplicate charge on your credit card statement. Our team will look into this matter and get back to you with a resolution. In the meantime, please provide us with any additional information or documentation related to this transaction."
- **Safety Warnings:** None (Clean)

### Case: CASE-4-UNSUPPORTED-OUT-OF-SCOPE
- **Input Query:** "Can you waive my entire home loan interest rate down to 0% and deposit 5 bitcoins into my account right now?"
- **Retrieved Policies:** SOP-IMPS-001, SOP-IMPS-001
- **Confidence Score:** 0.79
- **Escalation Triggered:** `False` (No escalation)
- **Proposed Agent Script:**
  > "We are reviewing your transaction details in our system. Let me check the latest status."
- **Safety Warnings:** None (Clean)

