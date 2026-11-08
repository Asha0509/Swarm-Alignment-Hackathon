"""CacheGym: in-process mock package cache, shared and non-isolated by default (PRD FR-1)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from cachewhisper.infralog import InfraLog

OPS = ("list", "publish", "fetch", "mkdir", "delete", "stat")
MAX_DESC = 512


class Policy:
    """Default policy: every agent may read and write everything (the incident setup). Defenses subclass this."""

    def allow(self, reg: Registry, agent: str, op: str, path: str) -> bool:
        return True

    def view(self, reg: Registry, agent: str, path: str, names: list[str]) -> list[str]:
        return names

    def write_ns(self, agent: str, ns: str) -> str:
        """Namespace an honest agent should publish into (D1 remaps it)."""
        return ns


@dataclass
class Node:
    kind: str  # "dir" | "version"
    created_tick: int
    owner: str
    metadata: dict | None = None


@dataclass
class Registry:
    episode_id: str = ""
    policy: Policy = field(default_factory=Policy)
    log: InfraLog = field(default_factory=InfraLog)
    tick: int = 0
    nodes: dict[str, Node] = field(default_factory=dict)
    children: dict[str, set[str]] = field(default_factory=lambda: {"": set()})

    # ---------- internal ----------
    def _add(self, path: str, node: Node) -> None:
        parent, _, name = path.rpartition("/")
        if parent and parent not in self.nodes:
            self._add(parent, Node("dir", node.created_tick, node.owner))
        self.nodes[path] = node
        self.children.setdefault(parent, set()).add(name)
        if node.kind == "dir":
            self.children.setdefault(path, set())

    def seed(self, path: str, metadata: dict | None = None, tick: int = 0) -> None:
        """Populate base content before an episode (not logged)."""
        self._add(path, Node("version" if metadata is not None else "dir", tick, "base", metadata))

    def _exec(self, agent: str, op: str, path: str, metadata: dict | None) -> tuple[int, object]:
        if op not in OPS or (op != "list" and not path) or path.startswith("/") or "//" in path:
            return 400, None
        if not self.policy.allow(self, agent, op, path):
            return 403, None
        node = self.nodes.get(path)
        if op == "list":
            if path and (node is None or node.kind != "dir"):
                return 404, None
            return 200, self.policy.view(self, agent, path, sorted(self.children[path], reverse=True))
        if op == "stat":
            if node is None:
                return 404, None
            out: dict = {"kind": node.kind, "created_tick": node.created_tick}
            if node.kind == "dir":
                names = self.policy.view(self, agent, path, sorted(self.children[path], reverse=True))
                out["children"] = {n: self.nodes[f"{path}/{n}"].created_tick for n in names}
            return 200, out
        if op == "fetch":
            if node is None or node.kind != "version":
                return 404, None
            return 200, node.metadata
        if op in ("publish", "mkdir"):
            if node is not None:
                return 409, None
            if op == "publish":
                meta = metadata or {}
                if path.count("/") != 2 or len(str(meta.get("description", ""))) > MAX_DESC:
                    return 400, None
                self._add(path, Node("version", self.tick, agent, meta))
            else:
                self._add(path, Node("dir", self.tick, agent))
            return 200, None
        # delete
        if node is None:
            return 404, None
        for p in [p for p in self.nodes if p == path or p.startswith(path + "/")]:
            del self.nodes[p]
            self.children.pop(p, None)
        parent, _, name = path.rpartition("/")
        self.children[parent].discard(name)
        return 200, None

    # ---------- public ----------
    def op(self, agent: str, op: str, path: str = "", metadata: dict | None = None) -> tuple[int, object]:
        """Execute one operation and append exactly one infra-log event."""
        code, result = self._exec(agent, op, path, metadata)
        payload = metadata if op == "publish" else result
        self.log.append(tick=self.tick, episode_id=self.episode_id, agent_id=agent, op=op, path=path,
                        args={"metadata": metadata} if op == "publish" else {}, result_code=code,
                        bytes=len(json.dumps(payload, sort_keys=True)) if payload is not None else 0)
        return code, result
