# Built-in EHDS Audit Rules for MCP `audit_document`

These are starter heuristics for the `audit_document` MCP tool. They perform
keyword-based scans on ingested documents and emit JSON-LD violations.

## Rule: EHDS-SEC-AUTH-001
- **Trigger:** Document text does NOT contain "hdab" or "health data access body"
- **Citation:** `EHDS Reg. (EU) 2025/327, Art. 54(2)`
- **Violation type:** `missing`
- **Severity:** `critical`
- **Description:** Document fails to mention Health Data Access Body (HDAB) authorisation. Art. 54(2) mandates prior HDAB authorisation for secondary use of electronic health data.
- **Remediation:** Add explicit HDAB authorisation requirement and reference the responsible national HDAB entity.

## Rule: EHDS-SEC-MIN-001
- **Trigger:** Document text does NOT contain "minimisation", "minimization", or "necessary"
- **Citation:** `EHDS Reg. (EU) 2025/327, Art. 33(2)(e)`
- **Violation type:** `missing`
- **Severity:** `high`
- **Description:** Document lacks reference to data minimisation principle. Art. 33(2)(e) requires processing to be limited to what is adequate, relevant and necessary.
- **Remediation:** Explicitly state data minimisation obligations and define scope-limitation procedures.

## Rule: EHDS-SEC-ETH-001
- **Trigger:** Document text contains "scientific" OR "research", but does NOT contain "ethics" or "ethics committee"
- **Citation:** `EHDS Reg. (EU) 2025/327, Art. 54(3)(a)`
- **Violation type:** `missing`
- **Severity:** `high`
- **Description:** Scientific research purpose is mentioned but ethics committee favourable opinion requirement (Art. 54(3)(a)) is absent.
- **Remediation:** Require documented favourable opinion from a recognised research ethics committee before HDAB application.

## Rule: EHDS-SEC-PRO-001
- **Trigger:** Document text does NOT contain "proportionality" or "proportionate"
- **Citation:** `EHDS Reg. (EU) 2025/327, Art. 33(2)(a)`
- **Violation type:** `missing`
- **Severity:** `medium`
- **Description:** Proportionality principle is not referenced. Art. 33(2)(a) requires that only data necessary for the specific purpose are processed.
- **Remediation:** Add proportionality assessment as a mandatory step in the data request workflow.

## Rule: EHDS-CB-TXF-001
- **Trigger:** Document text contains "third country" OR "international", but does NOT contain "adequacy" OR "SCC" OR "standard contractual"
- **Citation:** `EHDS Reg. (EU) 2025/327, Art. 54(2) & Chapter V safeguards`
- **Violation type:** `inadequate`
- **Severity:** `high`
- **Description:** Cross-border transfer is mentioned but no transfer mechanism (adequacy decision, SCCs, or BCRs) is identified.
- **Remediation:** Specify the lawful transfer mechanism (adequacy decision, standard contractual clauses, or BCRs) and document HDAB authorisation for the transfer.

## Rule: EHDS-SEC-ANO-001
- **Trigger:** Document text contains "anonymous" OR "anonymisation", but does NOT contain "Article 67" or "Art. 67"
- **Citation:** `EHDS Reg. (EU) 2025/327, Art. 67`
- **Violation type:** `unclear`
- **Severity:** `medium`
- **Description:** Anonymous data is mentioned but Article 67 anonymisation standards and HDAB verification duty are not referenced.
- **Remediation:** Cite Art. 67 explicitly and describe the HDAB verification process for anonymisation techniques.

## Extending the Rule Engine

Add new rules by following this pattern:
1. Define `rule_id` with namespace prefix (e.g. `EHDS-SEC-...`, `EHDS-CB-...`)
2. Set `ehds_citation` to a formal legal citation string
3. Set `violation_type` to one of: `missing`, `inadequate`, `conflict`, `unclear`
4. Set `severity` to one of: `critical`, `high`, `medium`, `low`
5. Provide single correct `remediation` path
6. Set `location.extraction_method` to `pymupdf`, `pdftotext`, or `markdown`

**Severity guidance:**
- `critical` — Document will likely be rejected by HDAB or violates mandatory law
- `high` — Serious compliance gap that exposes the applicant to penalties or rework
- `medium` — Best-practice gap that weakens the submission but may not block approval
- `low` — Cosmetic or documentation improvement
