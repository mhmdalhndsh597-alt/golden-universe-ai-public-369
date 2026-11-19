from __future__ import annotations

import base64
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from app.node_manager import NodeManager
from app.schemas import GpuTelemetry
from app.security import AuthenticationError, Ed25519NodeVerifier, SignedPayload


def b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


@pytest.fixture
def telemetry() -> GpuTelemetry:
    return GpuTelemetry(
        architecture="NVIDIA Hopper",
        driver_version="550.54.15",
        cuda_version="12.4",
        cuda_cores=16896,
        vram_gb=80,
        vram_free_gb=72,
        tflops_fp32=60,
        temperature_c=58,
        power_w=350,
        power_limit_w=700,
    )


def make_registration(
    verifier: Ed25519NodeVerifier,
    node_id: str = "gpu-node-01",
) -> tuple[SignedPayload, Ed25519PrivateKey]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    timestamp = int(time.time())
    nonce = "ab" * 16
    payload = SignedPayload(
        node_id=node_id,
        public_key_b64=b64(public_key),
        timestamp=timestamp,
        nonce=nonce,
        signature_b64="",
        context={"operation": "register"},
    )
    signature = private_key.sign(
        verifier.signed_message(payload, include_public_key=True)
    )
    return (
        SignedPayload(
            node_id=payload.node_id,
            public_key_b64=payload.public_key_b64,
            timestamp=payload.timestamp,
            nonce=payload.nonce,
            signature_b64=b64(signature),
            context=payload.context,
        ),
        private_key,
    )


def test_ed25519_registration_authentication() -> None:
    verifier = Ed25519NodeVerifier()
    payload, _ = make_registration(verifier)
    verifier.verify(payload)


def test_forged_node_is_rejected() -> None:
    verifier = Ed25519NodeVerifier()
    payload, _ = make_registration(verifier)
    forged = SignedPayload(
        node_id=payload.node_id,
        public_key_b64=payload.public_key_b64,
        timestamp=payload.timestamp,
        nonce="cd" * 16,
        signature_b64=payload.signature_b64,
        context=payload.context,
    )
    with pytest.raises(AuthenticationError, match="Invalid node signature"):
        verifier.verify(forged)


def test_replay_is_rejected() -> None:
    verifier = Ed25519NodeVerifier()
    payload, _ = make_registration(verifier)
    verifier.verify(payload)
    with pytest.raises(AuthenticationError, match="Replay detected"):
        verifier.verify(payload)


def test_nonce_cannot_be_reused_with_a_new_timestamp() -> None:
    current_time = [time.time()]
    verifier = Ed25519NodeVerifier(
        now=lambda: current_time[0], allowed_clock_skew_seconds=60
    )
    payload, private_key = make_registration(verifier)
    verifier.verify(payload)

    current_time[0] += 1
    replay = SignedPayload(
        node_id=payload.node_id,
        public_key_b64=payload.public_key_b64,
        timestamp=payload.timestamp + 1,
        nonce=payload.nonce,
        signature_b64="",
        context=payload.context,
    )
    replay = SignedPayload(
        node_id=replay.node_id,
        public_key_b64=replay.public_key_b64,
        timestamp=replay.timestamp,
        nonce=replay.nonce,
        signature_b64=b64(private_key.sign(verifier.signed_message(replay))),
        context=replay.context,
    )
    with pytest.raises(AuthenticationError, match="Replay detected"):
        verifier.verify(replay)


def test_signed_context_cannot_be_modified() -> None:
    verifier = Ed25519NodeVerifier()
    payload, _ = make_registration(verifier)
    modified = SignedPayload(
        node_id=payload.node_id,
        public_key_b64=payload.public_key_b64,
        timestamp=payload.timestamp,
        nonce="cd" * 16,
        signature_b64=payload.signature_b64,
        context={"operation": "register", "endpoint": "https://attacker.example"},
    )
    with pytest.raises(AuthenticationError, match="Invalid node signature"):
        verifier.verify(modified)


def test_tflops_weighted_load_balancer(telemetry: GpuTelemetry) -> None:
    manager = NodeManager()
    lower = telemetry.model_copy(update={"tflops_fp32": 40, "vram_free_gb": 40})
    higher = telemetry.model_copy(update={"tflops_fp32": 80, "vram_free_gb": 72})
    manager.register(
        node_id="gpu-a",
        endpoint="http://gpu-a.example/v1",
        public_key_ed25519="unused",
        region="eu",
        telemetry=lower,
    )
    manager.register(
        node_id="gpu-b",
        endpoint="http://gpu-b.example/v1",
        public_key_ed25519="unused",
        region="eu",
        telemetry=higher,
    )
    selected = manager.select_node("eu")
    assert selected is not None
    assert selected.node_id == "gpu-b"


def test_node_identity_cannot_be_taken_over(telemetry: GpuTelemetry) -> None:
    manager = NodeManager()
    manager.register(
        node_id="gpu-a",
        endpoint="https://gpu-a.example",
        public_key_ed25519="key-a",
        region="eu",
        telemetry=telemetry,
    )
    with pytest.raises(ValueError, match="already bound"):
        manager.register(
            node_id="gpu-a",
            endpoint="https://attacker.example",
            public_key_ed25519="key-b",
            region="eu",
            telemetry=telemetry,
        )


def test_inference_routing_rejects_capacity_when_no_node() -> None:
    manager = NodeManager()
    assert manager.select_node() is None
