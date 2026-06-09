"""Unit tests for GoodSenderClient — mocked HTTP via respx."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from langchain_goodsender.client import GoodSenderClient, GoodSenderError

BASE = "https://api.goodsender.com"


@pytest.fixture
def client() -> GoodSenderClient:
    return GoodSenderClient(api_key="test-key-123")


# -- send_template -----------------------------------------------------------


@respx.mock
def test_send_template_success(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/template").mock(
        return_value=Response(200, json={"status": "sent"})
    )
    result = client.send_template(
        template_id="otp_code",
        to_email="alice@example.com",
        subject="Your code",
        from_email="noreply@myapp.com",
        variables={"otp_code": "123456"},
    )
    assert result == {"status": "sent"}


@respx.mock
def test_send_template_nested_request_body(client: GoodSenderClient) -> None:
    route = respx.post(f"{BASE}/v1/emails/template").mock(
        return_value=Response(200, json={"status": "sent"})
    )
    client.send_template(
        template_id="otp_code",
        to_email="alice@example.com",
        to_name="Alice",
        subject="Your code",
        from_email="noreply@myapp.com",
        from_name="MyApp",
        variables={"otp_code": "123456", "app_name": "MyApp"},
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "from": {"email": "noreply@myapp.com", "name": "MyApp"},
        "to": {"email": "alice@example.com", "name": "Alice"},
        "subject": "Your code",
        "template": {
            "template_id": "otp_code",
            "variables": {"otp_code": "123456", "app_name": "MyApp"},
        },
    }


@respx.mock
def test_send_template_auth_failure(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/template").mock(
        return_value=Response(401, json={"error": "Invalid API key"})
    )
    with pytest.raises(GoodSenderError) as exc_info:
        client.send_template(
            template_id="otp_code",
            to_email="alice@example.com",
            subject="Your code",
            from_email="noreply@myapp.com",
        )
    assert exc_info.value.status_code == 401


@respx.mock
def test_send_template_not_found(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/template").mock(
        return_value=Response(404, json={"error": "Template not found"})
    )
    with pytest.raises(GoodSenderError) as exc_info:
        client.send_template(
            template_id="nonexistent",
            to_email="alice@example.com",
            subject="Test",
            from_email="noreply@myapp.com",
        )
    assert exc_info.value.status_code == 404


# -- send_email --------------------------------------------------------------


@respx.mock
def test_send_email_success(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/send").mock(
        return_value=Response(200, json={"sent": 1, "declined": 0})
    )
    result = client.send_email(
        to_email="bob@example.com",
        subject="Hello",
        from_email="hello@myapp.com",
        markdown_content="## Hi\nWelcome!",
    )
    assert result == {"sent": 1, "declined": 0}


@respx.mock
def test_send_email_declined(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/send").mock(
        return_value=Response(200, json={"sent": 0, "declined": 1})
    )
    result = client.send_email(
        to_email="bob@example.com",
        subject="Hello",
        from_email="hello@myapp.com",
        markdown_content="## Hi",
    )
    assert result["declined"] == 1
    assert result["sent"] == 0


# -- request_consent ---------------------------------------------------------


@respx.mock
def test_request_consent_success(client: GoodSenderClient) -> None:
    respx.post(f"{BASE}/v1/emails/consent").mock(
        return_value=Response(
            200,
            json={
                "emails": [
                    {"email": "bob@example.com", "domain": "myapp.com", "consentStatus": "requested"}
                ]
            },
        )
    )
    result = client.request_consent(domain="myapp.com", emails=["bob@example.com"])
    assert result["emails"][0]["consentStatus"] == "requested"


# -- check_consent -----------------------------------------------------------


@respx.mock
def test_check_consent(client: GoodSenderClient) -> None:
    respx.get(f"{BASE}/v1/emails/bob@example.com").mock(
        return_value=Response(
            200,
            json=[
                {"email": "bob@example.com", "domain": "myapp.com", "consentStatus": "granted"}
            ],
        )
    )
    result = client.check_consent("bob@example.com")
    assert result[0]["consentStatus"] == "granted"


# -- missing key -------------------------------------------------------------


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOODSENDER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key is required"):
        GoodSenderClient(api_key=None)
