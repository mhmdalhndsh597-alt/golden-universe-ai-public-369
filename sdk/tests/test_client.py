import unittest
from unittest.mock import Mock, patch

import httpx

from golden_universe_ai import GoldenUniverseClient


class GoldenUniverseClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.http = Mock()
        self.http.get.return_value.json.return_value = {"status": "healthy"}
        self.http.post.return_value.json.return_value = {"choices": []}
        self.client_factory = patch(
            "golden_universe_ai.httpx.Client", return_value=self.http
        )
        self.client_factory.start()
        self.addCleanup(self.client_factory.stop)
        self.client = GoldenUniverseClient("http://localhost:8000/")

    def test_health_uses_healthz_endpoint(self) -> None:
        self.assertEqual(self.client.health(), {"status": "healthy"})
        self.http.get.assert_called_once_with("/healthz")
        self.http.get.return_value.raise_for_status.assert_called_once()

    def test_chat_completions_uses_api_payload_and_optional_region(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]

        self.assertEqual(
            self.client.chat_completions("test-model", messages, region="eu"),
            {"choices": []},
        )
        self.http.post.assert_called_once_with(
            "/v1/chat/completions",
            params={"region": "eu"},
            json={"model": "test-model", "messages": messages},
        )
        self.http.post.return_value.raise_for_status.assert_called_once()

    def test_http_errors_are_propagated(self) -> None:
        self.http.get.return_value.raise_for_status.side_effect = (
            httpx.HTTPStatusError(
                "server error",
                request=httpx.Request("GET", "http://localhost:8000/healthz"),
                response=httpx.Response(500),
            )
        )

        with self.assertRaises(httpx.HTTPStatusError):
            self.client.health()


if __name__ == "__main__":
    unittest.main()
