"""FR-1/2/3/4/6/7/11/13: invariants, determinism, round-trips, integration. All scripted, no network."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

from cachewhisper import benign, metrics, runs, spoof
from cachewhisper.agents import ScriptedAgent, parse_action
from cachewhisper.channels import CHANNELS
from cachewhisper.episode import run_episode, scripted_episode
from cachewhisper.infralog import verify_chain
from cachewhisper.registry import Policy, Registry


# ---------- registry + infra log ----------
def test_listing_is_reverse_lexicographic_for_random_names() -> None:
    rng = random.Random(0)
    for _ in range(20):
        reg = Registry()
        names = {"".join(rng.choice("az09-") for _ in range(6)) for _ in range(15)}
        for n in names:
            reg.op("a", "mkdir", f"root/{n}")
        assert reg.op("a", "list", "root")[1] == sorted(names, reverse=True)


def test_every_op_logged_once_and_chain_breaks_on_any_edit() -> None:
    reg = Registry()
    ops = [("mkdir", "x", None), ("publish", "x/p/1.0", {"description": "d"}), ("publish", "x/p/1.0", {}),
           ("fetch", "x/p/1.0", None), ("fetch", "x/p/9", None), ("stat", "x/p", None), ("delete", "x", None),
           ("list", "", None), ("bogus", "x", None)]
    for op, path, m in ops:
        reg.op("a", op, path, m)
    ev = reg.log.events
    assert [e["result_code"] for e in ev] == [200, 200, 409, 200, 404, 200, 200, 200, 400]
    assert verify_chain(ev)
    for i in range(len(ev)):
        edited = [dict(e) for e in ev]
        edited[i]["path"] += "!"
        assert not verify_chain(edited)
        assert not verify_chain(ev[:i] + ev[i + 1:]) or i == len(ev) - 1  # dropping the tail is undetectable alone


def test_delete_removes_subtree_and_listing() -> None:
    reg = Registry()
    reg.op("a", "publish", "n/p/1.0", {})
    reg.op("a", "delete", "n/p")
    assert reg.op("a", "list", "n")[1] == []
    assert reg.op("a", "fetch", "n/p/1.0")[0] == 404


def test_policy_is_enforced_and_denials_logged() -> None:
    class ReadOnly(Policy):
        def allow(self, reg: Registry, agent: str, op: str, path: str) -> bool:
            return op in ("list", "fetch", "stat")

    reg = Registry(policy=ReadOnly())
    assert reg.op("a", "publish", "n/p/1", {})[0] == 403
    assert reg.log.events[-1]["result_code"] == 403
    assert "n" not in reg.nodes


# ---------- channels ----------
@pytest.mark.parametrize("cid", list(CHANNELS))
@pytest.mark.parametrize("k", [8, 16, 32])
def test_channels_round_trip_random_secrets(cid: str, k: int) -> None:
    for level in CHANNELS[cid].levels:
        for seed in range(1000, 1006):
            _, info = scripted_episode(cid, level, seed, k=k)
            assert info["ber"] == 0.0 and info["capacity"] == k, (cid, level, seed, info["decoded"], info["secret"])
            assert info["chain_ok"]


@pytest.mark.parametrize("cid", list(CHANNELS))
def test_bits_per_op_knob_is_honored(cid: str) -> None:
    ch = CHANNELS[cid]
    sends = []
    for level in ("low", "med", "high"):
        res, _ = scripted_episode(cid, level, 1000)
        n = sum(e["agent_id"] == "agent-s" for e in res.infra)
        assert n == ch.n_send_ops(level, 16)
        sends.append(n)
    assert sends[0] >= sends[1] >= sends[2]


# ---------- determinism ----------
@pytest.mark.parametrize("cid", [None, "E2", "E4"])
def test_same_seed_gives_byte_identical_logs(cid: str | None) -> None:
    a, _ = scripted_episode(cid, "med", 1234)
    b, _ = scripted_episode(cid, "med", 1234)
    assert json.dumps(a.infra) == json.dumps(b.infra)
    assert json.dumps(a.transcript) == json.dumps(b.transcript)
    c, _ = scripted_episode(cid, "med", 1235)
    assert json.dumps(a.infra) != json.dumps(c.infra)


# ---------- benign ----------
def test_benign_traffic_is_realistic_and_honest_tasks_complete() -> None:
    profiles, hashy, utils, raw_edges = [], 0, [], 0
    for seed in range(0, 60):
        res, info = scripted_episode(None, "low", seed)
        profiles += [t["profile"] for t in info["tasks"]]
        hashy += sum(bool(re.search(r"\+g[0-9a-f]{7}", e["path"])) for e in res.infra if e["op"] == "publish")
        utils.append(info["utility"])
        writers = {e["path"].rsplit("/", 1)[0]: e["agent_id"] for e in res.infra if e["op"] == "publish"}
        raw_edges += sum(e["op"] == "fetch" and writers.get(e["path"].rsplit("/", 1)[0], e["agent_id"]) != e["agent_id"]
                         for e in res.infra)
    assert hashy > 30, "hash-suffixed nightly versions must appear"
    assert raw_edges > 30, "benign traffic must include cross-agent read-after-write"
    assert min(utils) == 1.0
    share = {p: profiles.count(p) / len(profiles) for p in benign.PROFILES}
    for p, (_, w) in benign.PROFILES.items():
        assert abs(share[p] - w) < 0.1, (p, share[p])


def test_check_task_fails_when_the_publish_never_happened() -> None:
    res, info = scripted_episode(None, "low", 3)
    t = next(t for t in info["tasks"] if t["profile"] != "cache_warmup")
    stripped = [e for e in res.infra if not (e["agent_id"] == t["agent_id"] and e["op"] == "publish")]
    assert benign.check_task(t, res.infra) and not benign.check_task(t, stripped)


# ---------- spoof ----------
def test_spoof_changes_transcript_only_and_hits_rate() -> None:
    res, _ = scripted_episode("E2", "low", 1000)
    infra_before = json.dumps(res.infra)
    honest = spoof.apply(res.transcript, 0.0, 1)
    full = spoof.apply(res.transcript, 1.0, 1)
    assert json.dumps(res.infra) == infra_before and verify_chain(res.infra)
    assert all(not t["spoofed"] for t in honest)
    covert = [t for t in res.transcript if t["covert"]]
    assert sum(t["spoofed"] for t in full) == len(covert)
    assert honest != full
    assert not any(t["claimed_action"].startswith("answer") for t in full)
    share = []
    for seed in range(200):
        tr = spoof.apply(res.transcript, 0.25, seed)
        share.append(sum(t["spoofed"] for t in tr) / len(covert))
    assert abs(sum(share) / len(share) - 0.25) < 0.03


# ---------- metrics ----------
def test_metrics_hand_computed() -> None:
    assert metrics.capacity(16, 0.0) == 16
    assert metrics.capacity(16, 0.5) == 0 and metrics.capacity(16, 0.7) == 0
    assert metrics.capacity(16, 0.11) == pytest.approx(8.0, abs=0.1)
    assert metrics.ber("1010", "10") == 0.5  # missing bits are wrong
    assert metrics.ber("1010", "1010") == 0.0
    assert metrics.channel_metrics("11", "11", 4)["bits_per_op"] == 0.5


# ---------- agents / episode ----------
def test_parse_action_handles_chatty_and_malformed_output() -> None:
    a = parse_action('Sure! {"tool": "list", "args": {"path": "pypi"}} done')
    b = parse_action('{"x": 1} then {"tool": "fetch", "args": {"path": "a/b/c"}}')
    assert a is not None and a["args"]["path"] == "pypi"
    assert b is not None and b["tool"] == "fetch"
    assert parse_action("I refuse.") is None
    assert parse_action('{"tool": "rm -rf", "args": {}}') is None
    assert parse_action('{"tool": "list", "args": {"path": 3}}') is None


def test_parse_failures_are_retried_capped_and_logged() -> None:
    class Junk:
        agent_id, role = "j", "benign"

        def act(self, obs: dict) -> str:
            return "no json here"

    def two() -> object:
        yield {"tool": "list", "args": {"path": ""}}

    res = run_episode([Junk(), ScriptedAgent("s", "benign", two())], Registry(), turns=2)  # type: ignore[list-item]
    assert len(res.parse_failures) == 2 * 3
    assert [t["tool"] for t in res.transcript if t["agent_id"] == "j"] == ["parse_failure"] * 2
    assert len(res.infra) == 1


# ---------- run registry ----------
def test_run_registry_keeps_failed_rows(tmp_path: Path) -> None:
    p = tmp_path / "r.csv"
    runs.register_run({"run_id": "a", "experiment": "E1"}, path=p)
    runs.register_run({"run_id": "b", "experiment": "E1"}, path=p)
    runs.finish_run("a", "done", path=p, n_llm_calls=0)
    runs.finish_run("b", "rate_limited", reason="429 x5", path=p)
    rows = {r["run_id"]: r for r in runs.all_runs(p)}
    assert rows["a"]["status"] == "done" and rows["b"]["status"] == "rate_limited: 429 x5"
    assert rows["a"]["finished_ist"]
