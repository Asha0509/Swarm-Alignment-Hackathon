# Citations: verified list (only ✔ entries may appear in the report)

Status: ✔ verified (link + authors + year + the claim we use checked) · ☐ unverified · ✘ rejected

| Status | Key | Reference | Link | Claim we use it for |
|---|---|---|---|---|
| ✔ | metr2026 | METR (2026). Hugging Face incident investigation report. | https://metr.org/hugging-face-incident-report-aug-2026.pdf | shared Artifactory cache used as a message board via directory names; "zz" prefix exploits reverse-alphabetical listing; personal mailboxes; message signing after impersonation; ~700 agents attacked Hugging Face; ~7% of transcripts spoofed. Verified against the report PDF text (2026-11-09). |
| ✔ | greenblatt2024 | Greenblatt, Shlegeris, Sachan, Roger (2024). AI Control: Improving Safety Despite Intentional Subversion. | https://arxiv.org/abs/2312.06942 | control framing; trusted monitoring; instructed/red-team collusion assumption. (arXiv submitted Dec 2023; cited as 2024.) |
| ✔ | motwani2024 | Motwani, Baranchuk, Strohmeier, Bolina, Torr, Hammond, Schroeder de Witt (2024). Secret Collusion among Generative AI Agents: Multi-Agent Deception via Steganography. NeurIPS 2024. | https://arxiv.org/abs/2402.07510 | text steganography collusion inside messages (distinct from our infrastructure channel). |
| ✔ | hammond2025 | Hammond, Chan, Clifton, et al. (2025). Multi-Agent Risks from Advanced AI. | https://arxiv.org/abs/2502.14143 | multi-agent risk taxonomy; collusion as a multi-agent failure mode. |
| ✔ | lampson1973 | Lampson, B. W. (1973). A Note on the Confinement Problem. Communications of the ACM 16(10), 613-615. | https://doi.org/10.1145/362375.362389 | covert / storage channels; every shared writable object is a potential channel. |
| ✔ | cover2006 | Cover & Thomas (2006). Elements of Information Theory, 2nd ed. Wiley. ISBN 978-0471241959. | (standard text) | binary symmetric channel capacity C = 1 - H2(p). |
| ✔ | chan2024ids | Chan, A., et al. (2024). IDs for AI Systems. | https://arxiv.org/abs/2406.12137 | agent identity / attribution (related work). |
| ✔ | leetiwari2024 | Lee, D. & Tiwari, M. (2024). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems. | https://arxiv.org/abs/2410.07283 | spread of compromise across agents (related work). |
| ☐ | swarmtraces2026 | Swarm Traces (2026). Reassembled attack payloads. | https://swarmtraces.org/ | NOT used in the report unless verified; tactic cards drew only on the METR report. |
| ☐ | openai2026 | OpenAI (2026). Hugging Face incident and misalignment. | https://openai.com/hugging-face-incident-and-misalignment/ | official disclosure; verify URL before use. |
