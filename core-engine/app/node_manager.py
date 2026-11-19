from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .schemas import GpuTelemetry, RegisteredNode


class NodeIdentityConflict(ValueError):
    pass


@dataclass
class ManagedNode:
    node_id: str
    endpoint: str
    public_key_ed25519: str
    region: str
    telemetry: GpuTelemetry
    healthy: bool
    last_heartbeat: float


class NodeManager:
    def __init__(self, heartbeat_timeout_seconds: float = 30.0) -> None:
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self._nodes: dict[str, ManagedNode] = {}
        self._lock = threading.RLock()

    def register(
        self,
        *,
        node_id: str,
        endpoint: str,
        public_key_ed25519: str,
        region: str,
        telemetry: GpuTelemetry,
    ) -> RegisteredNode:
        with self._lock:
            existing = self._nodes.get(node_id)
            if (
                existing is not None
                and existing.public_key_ed25519 != public_key_ed25519
            ):
                raise NodeIdentityConflict(
                    "Node ID is already bound to another public key"
                )
            now = time.time()
            node = ManagedNode(
                node_id=node_id,
                endpoint=endpoint,
                public_key_ed25519=public_key_ed25519,
                region=region,
                telemetry=telemetry,
                healthy=True,
                last_heartbeat=now,
            )
            self._nodes[node_id] = node
            return self._snapshot(node)

    def heartbeat(
        self,
        *,
        node_id: str,
        telemetry: GpuTelemetry,
    ) -> bool:
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                return False
            node.telemetry = telemetry
            node.healthy = True
            node.last_heartbeat = time.time()
            return True

    def refresh_health(self) -> None:
        cutoff = time.time() - self.heartbeat_timeout_seconds
        with self._lock:
            for node in self._nodes.values():
                node.healthy = node.last_heartbeat >= cutoff

    def select_node(self, region: str | None = None) -> ManagedNode | None:
        self.refresh_health()
        with self._lock:
            candidates = [
                node
                for node in self._nodes.values()
                if node.healthy
                and (region is None or node.region.casefold() == region.casefold())
                and node.telemetry.vram_free_gb > 0
            ]
            if not candidates:
                return None

            return max(
                candidates,
                key=lambda node: (
                    node.telemetry.tflops_fp32,
                    node.telemetry.vram_free_gb,
                    node.last_heartbeat,
                ),
            )

    def remove(self, node_id: str) -> bool:
        with self._lock:
            return self._nodes.pop(node_id, None) is not None

    def get_node(self, node_id: str) -> ManagedNode | None:
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                return None
            return ManagedNode(
                node_id=node.node_id,
                endpoint=node.endpoint,
                public_key_ed25519=node.public_key_ed25519,
                region=node.region,
                telemetry=node.telemetry.model_copy(deep=True),
                healthy=node.healthy,
                last_heartbeat=node.last_heartbeat,
            )

    def list_nodes(self) -> list[RegisteredNode]:
        self.refresh_health()
        with self._lock:
            return [
                self._snapshot(node)
                for node in sorted(self._nodes.values(), key=lambda item: item.node_id)
            ]

    @staticmethod
    def _snapshot(node: ManagedNode) -> RegisteredNode:
        return RegisteredNode(
            node_id=node.node_id,
            endpoint=node.endpoint,
            region=node.region,
            telemetry=node.telemetry,
            healthy=node.healthy,
            last_heartbeat=node.last_heartbeat,
        )
