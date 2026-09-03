# FAP-Insurance Outreach Playbook

## Target Personas

1. **Independent Adjuster** — Handles 50-200 claims/month. Pain: spending hours verifying photo authenticity manually.
2. **SIU Manager** — Runs special investigations. Pain: proving timestamp fraud in court.
3. **Carrier VP of Claims** — Budget owner. Pain: $X million in photo fraud leakage annually.
4. **TPA Operations Director** — Manages third-party adjusters. Pain: no standardized photo verification across vendors.

---

## Cold Email Template #1 — Independent Adjuster

**Subject:** Cut your photo fraud review time by 80%

Hi [First Name],

I work with adjusters who are tired of playing detective with claimant photos.

One adjuster in Texas told me he spends 20 minutes per claim cross-referencing weather data, EXIF timestamps, and Google Street View to spot fabricated damage photos.

We built something that does it in 3 seconds.

FAP-Core checks every photo against:
• Live NOAA solar X-ray data (impossible to fabricate retroactively)
• Open-Meteo weather records for the claimed location/time
• Device enrollment status and witness consensus
• GPS plausibility against claimed location

**Real result from this morning:**
• Legitimate storm damage photo → 0.9175 / VERIFIED
• Same-looking fraud with fabricated timestamp → 0.3675 / QUARANTINE

**The pilot is free.** 1,000 verifications. No contract. No credit card.

Want to see it work on one of your open claims?

Best,
[Your Name]
FAP-Core | paslayco@gmail.com

P.S. — Here's a 90-second demo: [YouTube link]

---

## Cold Email Template #2 — SIU Manager

**Subject:** Your SIU team needs this solar anchor

[First Name],

Photo timestamp fraud is the hardest thing to prove in court. Claimants say "my phone was wrong" or "I don't know wigh the EXIF says that."

We built a verification system that doesn't rely on the phone at all.

It pulls the NOAA GOES X-ray flux for the exact minute the photo claims it was taken. That data is:
• Publicly logged forever
• Chaotic and impossible to predict
• Impossible to fabricate after the fact

If a photo claims it was taken at 2:47 PM on July 13th, we check what the sun was doing at 2:47 PM on July 13th. No match? The photo is lying about its birthday.

**Court-ready output:** Every verification generates a provenance hash, audit trail, and component breakdown. Your legal team gets a PDF report with NOAA record IDs.

Free pilot for SIU teams: 1,000 verifications.

Can I send you a sample report?

[Your Name]

---

## Cold Email Template #3 — Carrier VP of Claims

**Subject:** [Carrier Name] is losing $[X]M to photo fraud. Here's the math.

[First Name],

Industry data says 3-7% of property claims involve some form of photo manipulation or timestamp fraud.

If [Carrier Name] processes [N] claims/year at an average of $[Y] per claim, that's $[Z] million in leakage.

FAP-Core is a real-time photo provenance API that verifies every claim photo in under 3 seconds:

| Check | Source | Can It Be Faked? |
|-------|--------|------------------|
| Solar timestamp | NOAA GOES satellite | No |
| Weather match | Open-Meteo | No |
| Device enrollment | Cryptographic signature | Only with stolen device |
| Witness consensus | Multi-party attestation | Requires collusion |

**Pricing:** $0.08/verification at carrier volume. A single caught fraud case pays for 187,500 verifications.

**Pilot:** 1,000 free verifications. Run it on your next CAT event.

Can we schedule 15 minutes next week?

[Your Name]
FAP-Core

---

## LinkedIn Connection Request Scripts

**To Independent Adjuster:**
"Hi [Name] — I saw your post about [fraud case/storm event]. I built a tool that verifies claim photo timestamps against live NOAA solar data. Would love to show you how it caught a fabricated timestamp last week."

**To SIU Professional:**
"Hi [Name] — Your background in SIU caught my eye. I built a photo provenance engine that generates court-ready verification reports using NOAA satellite data. Would value your feedback on whether this would hold up in your investigations."

**To Carrier Executive:**
"Hi [Name] — I noticed [Carrier] processed [N] claims last quarter. I'm working on a photo verification API that caught $X in fraud during a pilot with a regional carrier. Would you be open to a 10-minute call about leakage reduction?"

---

## Follow-Up Sequence

**Day 3 (if no reply):**
"Quick follow-up — I know you're busy. Here's the 90-second demo video: [link]. The solar anchor part starts at 0:45."

**Day 7 (if no reply):**
"[First Name], one more thing — I'm running a free pilot for 10 adjusters this month. No strings. Just want real feedback from people who see photo fraud daily. Interested?"

**Day 14 (if no reply):**
"Last touch on this — if photo verification isn't a priority right now, I get it. If it becomes one in Q3, my email is paslayco@gmail.com."

---

## Objection Handling

**"We already have fraud detection."**
"Most carriers have rules-based fraud detection. FAP-Core is different — it verifies the physics of the photo itself. Not 'does this look suspicious?' but 'did the sun actually emit this X-ray flux at the claimed time?' It's a hard anchor, not a heuristic."

**"$0.08 per verification adds up."**
"At 50,000 verifications/month, that's $4,000. One caught fraud case at $15,000 pays for 3.75 years of verifications. The question isn't cost — it's how many fraud cases you're missing right now because you can't verify timestamps."

**"We need to run this through procurement/legal."**
"Absolutely. The pilot is free and requires no contract. Use it on 10 claims, show your legal team the audit trail, and then decide if you want to talk procurement. I'm not asking for a purchase — I'm asking for a test drive."

**"This sounds too good to be true."**
"I get that. The solar anchor isn't magic — it's just public data nobody was using for this. NOAA has been logging GOES X-ray flux since 1975. We're just the first to use it as a fraud detection signal. Happy to walk you through the API call so you can verify it yourself."
