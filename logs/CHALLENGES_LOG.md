# Challenges & Insights Log
Threats to validity, surprises, nulls, design trade-offs, and how we handled them.
Feeds: Limitations (Appendix A), Discussion, and the video.

<!-- TEMPLATE
## YYYY-MM-DD HH:MM IST — C### <title>
- **Category:** threat-to-validity | engineering | surprise | null result | rate-limit/time | dual-use
- **What happened:**
- **Why it matters for the claim:**
- **What we did:** (control added, analysis changed, claim scoped)
- **Use in report:** Limitations | Discussion | Methods | Appendix | video
-->

## Known threats going in
- C000a **Instructed collusion**: we measure capability, not propensity. Handled by explicit AI-control framing (Intro, Limitations).
- C000b **Weak benign traffic inflates monitors**: realistic scripted workloads with hash-like names, LLM-benign FPR transfer check, Adaption-invented scenarios.
- C000c **Detector tuned to our own attacks**: adaptive black-box LLM attacker with outcome-only feedback; expert channels designed before monitors were tuned.
- C000d **Open-weight models, not the incident's closed frontier models**: expert channels give an upper reference; the E5 model sweep shows the trend with scale; results framed as a lower bound.
- C000e **Spoofing is simulated** (no real container escape): stated in Methods and Limitations.
- C000f **Pre-shared protocol assumption**: standard in stego-collusion evals; stated in Limitations.
- C000g **Rate limits / throughput**: Adaption primary + free-tier rotation, disk cache, scripted agents wherever possible.
