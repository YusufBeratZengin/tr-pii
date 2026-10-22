---
name: Missed detection (False Negative)
about: Report personal data that tr-pii failed to detect or mask
title: '[FALSE NEGATIVE] '
labels: enhancement
assignees: ''
---

> [!CAUTION]
> **STRICT PRIVACY WARNING: NEVER PASTE REAL IDENTIFIERS**
> Never submit real Turkish ID numbers (TCKN), real tax numbers (VKN), real phone numbers, real bank IBANs, or confidential customer data.
> All reports must use synthetic dummy values (e.g. generated via `tr_pii.fake`) that reproduce the shape and delimiter format of the missed detection.

### PII Type

Which identifier type was missed?
(e.g., TCKN, VKN, IBAN, PHONE, EMAIL, CREDIT_CARD, PLATE, IP, POSTAL_CODE)

### Synthetic Reproduction Sample

Provide a synthetic, sanitized example demonstrating the issue:

```text
# Replace with synthetic dummy text (never real data!)
Example: "Tel: 5550000000" or synthetic text
```

### Expected Detection / Masking

What should `find()` or `mask()` have done?

```text
Expected match or masked output
```

### Actual Behavior

What was returned instead (e.g. empty findings, unmasked text)?

```text
Actual output
```

### Context and Surrounding Formatting

Describe the context (punctuation, spacing, prefix labels, or special characters) that caused the detector to overlook the candidate:
