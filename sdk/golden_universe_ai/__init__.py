from typing import Any, Mapping, Sequence

import httpx


class GoldenUniverseClient:
    """Client for the Golden Universe AI Center control-plane API."""

    def __init__(
        self, base_url: str = "http://localhost:8000", timeout: float = 30.0
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    def health(self) -> dict[str, Any]:
        response = self._client.get("/healthz")
        response.raise_for_status()
        return response.json()

    def chat_completions(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        *,
        region: str | None = None,
    ) -> dict[str, Any]:
        response = self._client.post(
            "/v1/chat/completions",
            params={"region": region} if region is not None else None,
            json={"model": model, "messages": list(messages)},
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GoldenUniverseClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


__all__ = ["GoldenUniverseClient"]
