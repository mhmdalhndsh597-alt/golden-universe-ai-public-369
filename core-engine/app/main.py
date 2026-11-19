from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Callable

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from .node_manager import NodeIdentityConflict, NodeManager
from .schemas import (
    ChatCompletionRequest,
    HealthResponse,
    Heartbeat,
    NodeRegistration,
)
from .security import AuthenticationError, Ed25519NodeVerifier, SignedPayload


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("guaigrid")
logger.addHandler(handler)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logger.propagate = False

node_manager = NodeManager(
    heartbeat_timeout_seconds=int(os.getenv("NODE_HEARTBEAT_TIMEOUT_SECONDS", "30"))
)
verifier = Ed25519NodeVerifier(
    allowed_clock_skew_seconds=int(os.getenv("SIGNED_REQUEST_CLOCK_SKEW", "30")),
)

REGISTERED_NODES = Gauge(
    "guaigrid_registered_nodes", "Total currently registered GPU nodes"
)
HEALTHY_NODES = Gauge("guaigrid_healthy_nodes", "Currently healthy GPU nodes")
INFERENCE_REQUESTS = Counter(
    "guaigrid_inference_requests_total",
    "OpenAI-compatible inference requests",
    ["status"],
)


class SlidingWindowRateLimit:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> tuple[bool, int]:
        async with self._lock:
            now = time.monotonic()
            bucket = self._requests[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                retry_after = max(1, int(bucket[0] + self.window_seconds - now))
                return False, retry_after
            bucket.append(now)
            return True, 0


rate_limiter = SlidingWindowRateLimit(
    limit=int(os.getenv("RATE_LIMIT_REQUESTS", "120")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GU-AI Grid control plane starting")
    yield
    logger.info("GU-AI Grid control plane stopped")


app = FastAPI(
    title="Golden Universe AI Center — GU-AI Grid",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next: Callable):
    if request.url.path in {"/metrics", "/healthz"}:
        return await call_next(request)
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = await rate_limiter.allow(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(retry_after)},
        )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    logger.warning("Authentication rejected", extra={"path": request.url.path})
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    nodes = node_manager.list_nodes()
    return HealthResponse(
        status="healthy",
        active_nodes=sum(1 for node in nodes if node.healthy),
        timestamp=time.time(),
    )


@app.get("/metrics")
async def metrics() -> Response:
    nodes = node_manager.list_nodes()
    REGISTERED_NODES.set(len(nodes))
    HEALTHY_NODES.set(sum(1 for node in nodes if node.healthy))
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/nodes/register", status_code=201)
async def register_node(payload: NodeRegistration):
    verifier.verify(
        SignedPayload(
            node_id=payload.node_id,
            public_key_b64=payload.public_key_ed25519,
            timestamp=payload.timestamp,
            nonce=payload.nonce,
            signature_b64=payload.signature,
            context=payload.model_dump(
                mode="json", exclude={"signature", "timestamp", "nonce"}
            ),
        )
    )
    try:
        return node_manager.register(
            node_id=payload.node_id,
            endpoint=str(payload.endpoint),
            public_key_ed25519=payload.public_key_ed25519,
            region=payload.region,
            telemetry=payload.telemetry,
        )
    except NodeIdentityConflict as exc:
        return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.post("/v1/nodes/{node_id}/heartbeat")
async def heartbeat(node_id: str, payload: Heartbeat):
    if payload.node_id != node_id:
        return JSONResponse(status_code=400, content={"detail": "Node ID mismatch"})
    node = node_manager.get_node(node_id)
    if node is None:
        return JSONResponse(status_code=404, content={"detail": "Unknown node"})
    verifier.verify(
        SignedPayload(
            node_id=payload.node_id,
            public_key_b64=node.public_key_ed25519,
            timestamp=payload.timestamp,
            nonce=payload.nonce,
            signature_b64=payload.signature,
            context=payload.model_dump(
                mode="json", exclude={"signature", "timestamp", "nonce"}
            ),
        ),
        include_public_key=False,
    )
    accepted = node_manager.heartbeat(
        node_id=payload.node_id,
        telemetry=payload.telemetry,
    )
    return {"accepted": accepted}


@app.get("/v1/nodes")
async def list_nodes():
    return {"nodes": node_manager.list_nodes()}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, region: str | None = None):
    node = node_manager.select_node(region)
    if node is None:
        INFERENCE_REQUESTS.labels(status="no_capacity").inc()
        return JSONResponse(status_code=503, content={"detail": "No healthy GPU capacity"})

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
        ) as client:
            upstream = await client.post(
                f"{node.endpoint.rstrip('/')}/v1/chat/completions",
                json=request.model_dump(mode="json"),
            )
            upstream.raise_for_status()
    except httpx.TimeoutException:
        INFERENCE_REQUESTS.labels(status="timeout").inc()
        return JSONResponse(status_code=504, content={"detail": "Inference node timeout"})
    except httpx.HTTPError as exc:
        INFERENCE_REQUESTS.labels(status="upstream_error").inc()
        logger.error("Inference upstream failed", extra={"node_id": node.node_id})
        return JSONResponse(
            status_code=502,
            content={"detail": "Inference node request failed"},
        )

    INFERENCE_REQUESTS.labels(status="success").inc()
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
