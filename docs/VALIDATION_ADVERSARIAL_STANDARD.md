# FAP-Insurance Verify — Adversarial Validation Standard

## Purpose

The request boundary is a security and evidence-integrity boundary. Invalid, ambiguous, oversized, or internally inconsistent input must be rejected before verification logic or external oracles are invoked.

## Fail-closed contract

A request is admissible only when all of the following hold:

- Required identity fields are present, typed as strings, non-blank after normalization, and bounded in size.
- Coordinates are finite numbers within geographic bounds and reject `(0, 0)`.
- `timestamp_claimed` is a timezone-aware ISO datetime and is not in the future.
- A supplied media hash is exactly 64 hexadecimal characters and therefore syntactically consistent with SHA-256.
- Witness IDs are strings, non-blank, unique, and bounded; at most 10 are accepted.
- Optional policy and note fields are bounded and non-blank when supplied.
- Unknown JSON fields are rejected rather than silently ignored.
- Media URL input is bounded and non-blank when supplied.

## Adversarial classes

The test suite intentionally exercises:

1. Type confusion and null injection.
2. Numeric boundary violations, NaN, and infinity.
3. Impossible/ambiguous temporal input.
4. Hash length and character-set violations.
5. Duplicate, blank, null, and excessive witnesses.
6. Blank identity fields and oversized strings.
7. Unknown-field injection.
8. Valid boundary controls to prevent over-validation.

## Standard

A green test run demonstrates that the tested attack classes are contained at the request-model boundary. It does not constitute a general security certification. New fields or trust-bearing inputs require corresponding adversarial cases before release.
