# Project Roadmap | خارطة طريق المشروع

This roadmap is directional; planned items may change based on community
feedback and implementation priorities.

هذه الخارطة استرشادية وقد تتغير الأولويات وفقاً لملاحظات المجتمع ومتطلبات
التنفيذ.

## v1.0 — Community Core

- Ed25519-signed GPU node registration with timestamp and nonce replay
  protection.
- GPU telemetry and node health tracking.
- Routing of OpenAI-compatible chat-completion requests to healthy nodes.
- Prometheus metrics and a Next.js web console.
- AGPLv3 community core with proprietary enterprise components maintained
  separately.

## v1.1 — Developer Ecosystem

- [x] Python client SDK for health checks and chat completions.
- [ ] Node.js client SDK.
- [ ] Real-time WebSocket GPU telemetry streaming.
- [ ] Automated multi-region node discovery.

## v2.0 — Federated Inference

- [ ] Expanded native LLM, audio, and vision inference pipelines.
- [ ] Federated compute coordination and settlement.
