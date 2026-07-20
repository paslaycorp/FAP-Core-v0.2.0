# FAP — Fact-Artifact Protocol
## Deepfake Prevention at the Moment of Creation

> *"Don't authenticate the image. Authenticate the moment it was born."*

## The Problem

We've spent a decade building better lie detectors. But detection is an arms race the defender cannot win. The forger only needs to succeed once. We need to succeed every time.

## The Insight

**FAP** stops deepfakes before they exist.

When FAP captures a photo, it calls **six independent witnesses** from six different domains to cryptographically attest to the moment of creation.

## The Six Witnesses

| Witness | Attests | Why It Matters |
|---------|---------|---------------|
| **Temporal** | Precise UTC timestamp | Proves *when* |
| **Spatial** | GPS + altitude + bearing | Proves *where* |
| **Device** | Hardware fingerprint + secure enclave | Proves *with what* |
| **Network** | TLS certificate chain + DNS path | Proves *via which path* |
| **User** | Biometric intent + voluntary attestation | Proves *by whom, willingly* |
| **AI** | On-device content analysis + provenance hash | Proves *what was captured* |

## Why This Is Different

| Approach | When It Works | Vulnerability |
|----------|--------------|---------------|
| Watermarking | After creation | Strip in Photoshop |
| Metadata | After creation | Remove with screenshot |
| AI Detection | After creation | Train better AI to fool it |
| **FAP** | **At creation** | Requires compromising 6 independent systems + distributed ledger |

## License

AGPL-3.0

---

> *"The forger only needs to succeed once. We need to succeed every time."*
>
> — Patrick, Architect
