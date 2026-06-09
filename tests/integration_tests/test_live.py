"""Integration tests — live GoodSender API calls.

Skipped unless GOODSENDER_API_KEY is set in the environment.
"""

from __future__ import annotations

import os

import pytest

from langchain_goodsender import GoodSenderClient, GoodSenderToolkit

SKIP_REASON = "GOODSENDER_API_KEY not set"
has_key = bool(os.environ.get("GOODSENDER_API_KEY"))


@pytest.fixture
def client() -> GoodSenderClient:
    return GoodSenderClient()


@pytest.mark.skipif(not has_key, reason=SKIP_REASON)
class TestLiveTemplate:
    def test_send_otp_template(self, client: GoodSenderClient) -> None:
        result = client.send_template(
            template_id="otp_code",
            to_email="constantine+gs-no-consent@joylabsventures.com",
            subject="Integration test OTP",
            from_email="noreply@goodsender.com",
            variables={"otp_code": "000000", "app_name": "CI Test"},
        )
        assert result.get("status") == "sent"

    @pytest.mark.asyncio
    async def test_send_otp_template_async(self, client: GoodSenderClient) -> None:
        result = await client.asend_template(
            template_id="otp_code",
            to_email="constantine+gs-no-consent@joylabsventures.com",
            subject="Integration test OTP async",
            from_email="noreply@goodsender.com",
            variables={"otp_code": "000000", "app_name": "CI Test"},
        )
        assert result.get("status") == "sent"


@pytest.mark.skipif(not has_key, reason=SKIP_REASON)
class TestLiveConsent:
    def test_request_consent(self, client: GoodSenderClient) -> None:
        result = client.request_consent(
            domain="kostya-gs-prod.test.dev.laneful.net",
            emails=["constantine+gs@joylabsventures.com"],
        )
        assert "emails" in result


@pytest.mark.skipif(not has_key, reason=SKIP_REASON)
class TestLiveToolkit:
    def test_tools_bind(self) -> None:
        toolkit = GoodSenderToolkit()
        tools = toolkit.get_tools()
        assert len(tools) == 3
        for tool in tools:
            schema = tool.args_schema.model_json_schema()
            assert "properties" in schema
