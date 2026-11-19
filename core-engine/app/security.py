from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


NONCE_TTL_SECONDS = 300


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True)
class SignedPayload:
    node_id: str
    public_key_b64: str
    timestamp: int
    nonce: str
    signature_b64: str
    context: dict[str, object] | None = None

    def replay_identity(self) -> str:
        return f"{self.node_id}:{self.nonce}"


class Ed25519NodeVerifier:
    def __init__(
        self,
        *,
        allowed_clock_skew_seconds: int = 30,
        nonce_ttl_seconds: int = NONCE_TTL_SECONDS,
        now: Callable[[], float] = time.time,
    ) -> None:
        self.allowed_clock_skew_seconds = allowed_clock_skew_seconds
        self.nonce_ttl_seconds = nonce_ttl_seconds
        self._now = now
        self._seen_nonces: dict[str, float] = {}
        self._lock = threading.Lock()

    def _decode_public_key(self, value: str) -> Ed25519PublicKey:
        try:
            raw = base64.b64decode(value, validate=True)
            if len(raw) != 32:
                raise AuthenticationError("Ed25519 public key must be 32 bytes")
            return Ed25519PublicKey.from_public_bytes(raw)
        except AuthenticationError:
            raise
        except Exception as exc:
            raise AuthenticationError("Invalid Ed25519 public key encoding") from exc

    @staticmethod
    def signed_message(
        payload: SignedPayload, *, include_public_key: bool = True
    ) -> bytes:
        message: dict[str, object] = {
            "node_id": payload.node_id,
            "timestamp": payload.timestamp,
            "nonce": payload.nonce,
            "context": payload.context or {},
        }
        if include_public_key:
            message["public_key_ed25519"] = payload.public_key_b64
        return json.dumps(
            message, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def verify(
        self, payload: SignedPayload, *, include_public_key: bool = True
    ) -> None:
        now = int(self._now())
        if abs(now - payload.timestamp) > self.allowed_clock_skew_seconds:
            raise AuthenticationError("Timestamp outside allowed clock skew")

        replay_key = hashlib.sha256(payload.replay_identity().encode()).hexdigest()
        with self._lock:
            cutoff = now - self.nonce_ttl_seconds
            self._seen_nonces = {
                key: seen_at
                for key, seen_at in self._seen_nonces.items()
                if seen_at >= cutoff
            }
            if replay_key in self._seen_nonces:
                raise AuthenticationError("Replay detected")

            public_key = self._decode_public_key(payload.public_key_b64)
            try:
                signature = base64.b64decode(payload.signature_b64, validate=True)
                if len(signature) != 64:
                    raise AuthenticationError("Ed25519 signature must be 64 bytes")
                public_key.verify(
                    signature,
                    self.signed_message(
                        payload, include_public_key=include_public_key
                    ),
                )
            except AuthenticationError:
                raise
            except InvalidSignature as exc:
                raise AuthenticationError("Invalid node signature") from exc
            except Exception as exc:
                raise AuthenticationError("Invalid signature encoding") from exc
            self._seen_nonces[replay_key] = now
