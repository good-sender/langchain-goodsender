"""Unit tests for GoodSender LangChain tools — mocked HTTP via respx."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from langchain_goodsender import (
    GoodSenderSendTemplateTool,
    GoodSenderSendEmailTool,
    GoodSenderRequestConsentTool,
    GoodSenderClient,
    GoodSenderToolkit,
)

BASE = "https://api.goodsender.com"


@pytest.fixture
def client() -> GoodSenderClient:
    return GoodSenderClient(api_key="test-key")


# -- GoodSenderSendTemplateTool ----------------------------------------------


@respx.mock
def test_send_template_tool(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/template").mock(
        return_value=Response(200, json={"status": "sent"})
    )
    tool = GoodSenderSendTemplateTool(client=client)
    result = tool.invoke(
        {
            "template_id": "otp_code",
            "to_email": "alice@test.com",
            "subject": "Your code",
            "from_email": "noreply@myapp.com",
            "variables": {"otp_code": "999"},
        }
    )
    assert "sent" in result.lower()
    assert "otp_code" in result


@respx.mock
@pytest.mark.asyncio
async def test_send_template_tool_async(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/template").mock(
        return_value=Response(200, json={"status": "sent"})
    )
    tool = GoodSenderSendTemplateTool(client=client)
    result = await tool.ainvoke(
        {
            "template_id": "mfa_enrollment",
            "to_email": "alice@test.com",
            "subject": "MFA",
            "from_email": "noreply@myapp.com",
        }
    )
    assert "sent" in result.lower()


# -- GoodSenderSendEmailTool -------------------------------------------------


@respx.mock
def test_send_email_tool(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/send").mock(
        return_value=Response(200, json={"sent": 1, "declined": 0})
    )
    tool = GoodSenderSendEmailTool(client=client)
    result = tool.invoke(
        {
            "to_email": "bob@test.com",
            "subject": "Hello",
            "from_email": "hello@myapp.com",
            "markdown_content": "# Welcome",
        }
    )
    assert "1 sent" in result
    assert "0 declined" in result


@respx.mock
def test_send_email_tool_declined(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/send").mock(
        return_value=Response(200, json={"sent": 0, "declined": 1})
    )
    tool = GoodSenderSendEmailTool(client=client)
    result = tool.invoke(
        {
            "to_email": "bob@test.com",
            "subject": "Hello",
            "from_email": "hello@myapp.com",
            "markdown_content": "# Welcome",
        }
    )
    assert "0 sent" in result
    assert "1 declined" in result


# -- GoodSenderRequestConsentTool --------------------------------------------


@respx.mock
def test_request_consent_tool(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/consent").mock(
        return_value=Response(
            200,
            json={
                "emails": [
                    {"email": "bob@test.com", "domain": "myapp.com", "consentStatus": "requested"}
                ]
            },
        )
    )
    tool = GoodSenderRequestConsentTool(client=client)
    result = tool.invoke({"domain": "myapp.com", "emails": ["bob@test.com"]})
    assert "requested" in result


# -- Toolkit -----------------------------------------------------------------


def test_toolkit_returns_three_tools() -> None:
    toolkit = GoodSenderToolkit(api_key="test-key")
    tools = toolkit.get_tools()
    assert len(tools) == 3
    names = {t.name for t in tools}
    assert names == {
        "goodsender_send_template",
        "goodsender_send_email",
        "goodsender_request_consent",
    }


# -- Schema validation -------------------------------------------------------


def test_tools_have_pydantic_schemas() -> None:
    toolkit = GoodSenderToolkit(api_key="test-key")
    for tool in toolkit.get_tools():
        schema = tool.args_schema
        assert schema is not None
        json_schema = schema.model_json_schema()
        assert "properties" in json_schema
