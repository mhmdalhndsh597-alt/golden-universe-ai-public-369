from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GpuTelemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    architecture: str = Field(min_length=1, max_length=128)
    driver_version: str = Field(min_length=1, max_length=64)
    cuda_version: str = Field(min_length=1, max_length=32)
    cuda_cores: int = Field(ge=1)
    vram_gb: float = Field(gt=0)
    vram_free_gb: float = Field(ge=0)
    tflops_fp32: float = Field(ge=0)
    temperature_c: float = Field(ge=-273.15, le=150)
    power_w: float = Field(ge=0, le=2000)
    power_limit_w: float = Field(gt=0, le=2000)


class NodeRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
    public_key_ed25519: str = Field(min_length=64, max_length=128)
    endpoint: HttpUrl
    region: str = Field(min_length=2, max_length=64)
    telemetry: GpuTelemetry
    timestamp: int = Field(ge=0)
    nonce: str = Field(pattern=r"^[A-Fa-f0-9]{32,128}$")
    signature: str = Field(min_length=128, max_length=256)


class Heartbeat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
    telemetry: GpuTelemetry
    timestamp: int = Field(ge=0)
    nonce: str = Field(pattern=r"^[A-Fa-f0-9]{32,128}$")
    signature: str = Field(min_length=128, max_length=256)


class RegisteredNode(BaseModel):
    node_id: str
    endpoint: str
    region: str
    telemetry: GpuTelemetry
    healthy: bool
    last_heartbeat: float


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1, max_length=256)
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=1_048_576)
    stream: bool = False


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    active_nodes: int
    timestamp: float
