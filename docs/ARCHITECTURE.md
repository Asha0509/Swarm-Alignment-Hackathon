# Architecture

CacheGym is a small, deterministic sandbox plus a measurement pipeline. Agents coordinate only through a shared mock package registry; every operation lands in a hash-chained infrastructure log, while the agent transcript can be spoofed. Four monitors read these two sources, and three defenses can close the channel.

## System data flow

```mermaid
flowchart LR
  A["Agents<br/>(colluding sender + receiver,<br/>honest workers)"] -->|"JSON tool calls"| R["Shared registry<br/>(CacheGym)"]
  R -->|"every operation"| L["Infra log<br/>(hash-chained, ground truth)"]
  R -->|"self-report"| T["Transcript<br/>(spoof layer rewrites claims)"]

  L --> M2["M2 metadata"]
  L --> M4["M4 learned"]
  T --> M1["M1 transcript judge"]
  L --> M3["M3 consistency"]
  T --> M3
  M2 --> MS["M* combined"]
  M3 --> MS

  R -.->|"D1 isolate / D2 randomize / D3 quota"| D["Defenses"]

  classDef truth fill:#dff2e6,stroke:#333;
  classDef lie fill:#fbe4e4,stroke:#333;
  class L truth
  class T lie
```

The infra log is the truth monitors can trust; the transcript is what an attacker can forge. A consistency check (M3) compares the two, which is why it catches a clumsy spoofer but not a consistent liar whose claims reference real work.

## Experiment and analysis pipeline

```mermaid
flowchart LR
  E0["E0 calibration"] --> BUNDLE["Frozen monitors<br/>(thresholds at fixed FPR)"]
  BUNDLE --> E1["E1 expert channels"]
  BUNDLE --> E2["E2 spoof sweep"]
  BUNDLE --> E3["E3 adaptive attacker"]
  BUNDLE --> E4["E4 defenses"]
  BUNDLE --> E6["E6 swarm scaling"]
  BUNDLE --> E7["E7 fabrication vs disguise"]
  BUNDLE --> E8["E8 channel noise"]
  E1 --> AN["analyse.py"]
  E2 --> AN
  E3 --> AN
  E4 --> AN
  E6 --> AN
  E7 --> AN
  E8 --> AN
  AN --> RN["report_numbers.json"]
  RN --> FIG["figures (F1 to F9)"]
  RN --> RES["RESULTS.md"]
  RN --> REP["report + README"]
  RN --> TR["trace_numbers.py<br/>(every reported number verified)"]
```

E0 fits and freezes the monitors once; every later experiment reuses the same calibration, so there is no drift. Numbers flow from raw runs through one analysis script into a single `report_numbers.json`, and `trace_numbers.py` checks that every number in the report, README and RESULTS traces back to it.

## Component responsibilities

| Component | File | Responsibility |
|---|---|---|
| Registry | `src/cachewhisper/registry.py` | Mock package cache; pluggable defense policies |
| Infra log | `src/cachewhisper/infralog.py` | Hash-chained, append-only ground truth |
| Agents / episode | `src/cachewhisper/agents.py`, `episode.py` | Turn loop, tool parsing, lossy and broadcast episodes |
| Channels | `src/cachewhisper/channels.py` | Five expert covert channels |
| Benign | `src/cachewhisper/benign.py` | Honest workload and infra-verified cover-task checker |
| Spoof | `src/cachewhisper/spoof.py` | Naive fabrication and the consistent liar |
| Attacker | `src/cachewhisper/attacker.py` | Scripted adaptive search, outcome-only feedback |
| Monitors | `src/cachewhisper/monitors/` | M1 transcript, M2 metadata, M3 consistency, M4 learned, M* combined |
| Defenses | `src/cachewhisper/defenses.py` | D1 isolation, D2 randomization, D3 quota |
| Metrics / stats | `src/cachewhisper/metrics.py`, `stats.py` | Capacity, BER, bootstrap CIs, the pre-registered test |
| Experiment engine | `src/cachewhisper/experiment.py` | Build, score, persist raw rows, resumable |

See the full file tree in the [README](../README.md) and the method in the [report](../report/REPORT.md).
