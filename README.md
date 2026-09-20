# FAP-Core

**Bounded evidence verification component for the FAP architecture**

FAP-Core accepts structured artifact claims, evaluates configured provenance and environmental signals, and returns a verification result with component evidence. It is an evidence-producing service; it is not the EPM decision authority and does not by itself authorize downstream action.

## Current runtime line

- component version: `0.2.0`
- production source line: exact-SHA deployments from merged GitHub history
- production deployment authority: repository release workflow
- production API authentication: bearer credential
- canonical health surface: `/health`

The current production-authority commit remains separately verifiable from deployment evidence. Repository governance work is tracked independently from runtime semantics.

## Service surfaces

The FastAPI service currently exposes:

- `/` — service landing surface
- `/demo` — bounded demonstration scenarios
- `/health` — component health/version response
- `/verify` — authenticated verification request
- `/enroll` — authenticated device-enrollment surface

Production documentation exposure is intentionally restricted by environment configuration.

## Evidence boundary

FAP-Core can evaluate signals such as artifact hashes, claimed time/location, device information, witnesses, and configured oracle observations.

A FAP-Core score or verdict is not automatically:

- proof that an event occurred exactly as claimed;
- EPM authorization;
- jurisdictional permission;
- policy authority;
- proof that evidence was available to an earlier decision state.

Those boundaries belong to the consuming assurance layer.

## EPM interoperability

The staged EPM/FAP contract treats FAP-Core as a **bounded evidence producer**.

The forward contract is designed to preserve:

- exact producer identity;
- evidence identity;
- temporal fields;
- explicit boundary-validation state;
- separation of evidence receipts from EPM decision receipts.

FAP-Core does not gain EPM transition authority merely by producing a valid receipt.

## Failure posture

Production integration is expected to fail closed when a required dependency or verification boundary cannot be established. Operational availability must not be converted into semantic certainty, and transient infrastructure failures must not be reclassified as successful evidence.

## Development

Install dependencies and run the repository test suite before proposing a merge. Production releases should remain exact-SHA and traceable to merged pull-request history.

## License

AGPL-3.0.
