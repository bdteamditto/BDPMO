# Crisis / Emergency Handover

Crisis Handover is used when the person currently holding a project cannot continue normal project ownership and another project member needs enough context to take over immediately.

## What is recorded

- original project owner
- acting / takeover owner
- reason for emergency handover
- Critical Next Actions
- dependencies and items currently waiting on another party
- important contacts
- latest communication
- important documents / links
- activation, acceptance, and closure timestamps

The acting owner receives an in-app notification and must explicitly select **รับช่วงงาน**. Activation, updates, acceptance, and closure are retained in the project audit timeline.

## Permissions

OWNER and EDITOR members can open or update Crisis Handover. The original owner and acting owner must already be members of the same project. VIEWER remains read-only. Only the member selected as acting owner can accept the handover.

## Persistent Debt example

For project **6926-Persistent Debt**, the current working point discussed for the pilot is milestone **2-2 Development & SIT**, contract **64006992**, signed **2 July 2026**. The four deliverables for this milestone are:

1. Detailed Specification Document
2. Unit & SIT Test Report
3. deploy the SIT-tested program to UAT
4. Source Code Scan Report

The contractual due date is **30 October 2026**. Test Plan, Test Case, and Test Procedure are prerequisites, with customer review at least 7 days before testing.

A current dependency example is the vendor-contract chain. The customer contract is signed, while the vendor contract is not yet signed and vendor information has already been sent to Legal. Crisis Handover should therefore record the Legal dependency, owner/status/date, next follow-up action, and the relevant document or communication link instead of treating “sent to Legal” as completed work.
