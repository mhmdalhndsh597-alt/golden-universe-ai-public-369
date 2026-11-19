<div align="center">

# 🌟 Golden Universe AI Center
### مركز الكون AI الذهبي

**GU-AI Grid | Distributed GPU orchestration and inference**

*منصة لتنسيق وحدات معالجة الرسومات الموزعة وتمرير طلبات الاستدلال*

[![License: AGPL v3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](LICENSE)

</div>

GU-AI Grid is an open-core platform for registering GPU nodes, tracking node
health and telemetry, and routing OpenAI-compatible chat-completion requests
to healthy workers. The community core is licensed under AGPLv3. Proprietary
enterprise components are not included in this public repository.

منصة GU-AI Grid مفتوحة النواة لتسجيل عقد GPU ومتابعة حالتها وبياناتها، وتوجيه
طلبات إكمال المحادثات المتوافقة مع OpenAI إلى العقد السليمة. نواة المجتمع
مرخصة بموجب AGPLv3، ولا تتضمن هذه المستودعات العامة مكونات المؤسسات الاحتكارية.

## Architecture | المعمارية

```text
Next.js web console
        |
FastAPI control plane
  | node registry, health and metrics
  | OpenAI-compatible chat-completion routing
        |
Registered GPU inference workers
```

The control plane exposes a health endpoint, Prometheus metrics, signed node
registration and heartbeat endpoints, node listing, and chat-completion
routing. See the [API documentation](http://localhost:8000/docs) when running
the service locally.

## Quick start | التشغيل السريع

```bash
make setup
make test
make run-core
```

Or start the containerized services:

```bash
docker compose -f deploy/docker-compose.yml up -d
```

Install the Python client SDK from this repository:

```bash
python -m pip install ./sdk
```

```python
from golden_universe_ai import GoldenUniverseClient

with GoldenUniverseClient("http://localhost:8000") as client:
    health = client.health()
    completion = client.chat_completions(
        model="your-model",
        messages=[{"role": "user", "content": "Hello"}],
    )
```

## Roadmap | خارطة الطريق

See [ROADMAP.md](ROADMAP.md) for current capabilities and planned work.

## Contributing | المساهمة

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Contributor License Agreement](legal/CLA.md) before submitting a contribution.
The [issue templates](.github/ISSUE_TEMPLATE/) and
[pull request template](.github/PULL_REQUEST_TEMPLATE.md) are bilingual.
