"""Thin httpx client for the GoodSender email API (sync + async)."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.goodsender.com"
DEFAULT_TIMEOUT = 30.0

TEMPLATE_IDS = (
    "mfa_enrollment",
    "new_device_login",
    "order_completed",
    "otp_code",
    "email_changed",
    "password_changed",
    "order_receipt",
)


class GoodSenderError(Exception):
    """Raised when the GoodSender API returns a non-2xx response."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"GoodSender API error {status_code}: {body}")


class GoodSenderClient:
    """Sync + async client for the GoodSender REST API.

    Args:
        api_key: GoodSender API key. Falls back to ``GOODSENDER_API_KEY`` env var.
        base_url: API base URL. Defaults to ``https://api.goodsender.com``.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = api_key or os.environ.get("GOODSENDER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "A GoodSender API key is required. Pass it directly or set "
                "the GOODSENDER_API_KEY environment variable."
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # -- internal helpers ------------------------------------------------

    def _sync_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout,
        )

    def _async_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout,
        )

    @staticmethod
    def _handle_response(resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            raise GoodSenderError(resp.status_code, resp.text)
        return resp.json()

    # -- sync methods ----------------------------------------------------

    def send_template(
        self,
        *,
        template_id: str,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "from": {"email": from_email, **({"name": from_name} if from_name else {})},
            "to": {"email": to_email, **({"name": to_name} if to_name else {})},
            "subject": subject,
            "template": {
                "template_id": template_id,
                **({"variables": variables} if variables else {}),
            },
        }
        with self._sync_client() as c:
            return self._handle_response(c.post("/v1/emails/template", json=body))

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        markdown_content: str | None = None,
        html_content: str | None = None,
        text_content: str | None = None,
    ) -> dict[str, Any]:
        email_obj: dict[str, Any] = {
            "from": {"email": from_email, **({"name": from_name} if from_name else {})},
            "to": [{"email": to_email, **({"name": to_name} if to_name else {})}],
            "subject": subject,
        }
        if markdown_content:
            email_obj["markdown_content"] = markdown_content
        elif html_content:
            email_obj["html_content"] = html_content
        elif text_content:
            email_obj["text_content"] = text_content
        with self._sync_client() as c:
            return self._handle_response(c.post("/v1/emails/send", json={"emails": [email_obj]}))

    def request_consent(
        self,
        *,
        domain: str,
        emails: list[str],
    ) -> dict[str, Any]:
        with self._sync_client() as c:
            return self._handle_response(
                c.post("/v1/emails/consent", json={"domain": domain, "emails": emails})
            )

    def check_consent(self, email: str) -> list[dict[str, Any]]:
        with self._sync_client() as c:
            return self._handle_response(c.get(f"/v1/emails/{email}"))

    # -- async methods ---------------------------------------------------

    async def asend_template(
        self,
        *,
        template_id: str,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "from": {"email": from_email, **({"name": from_name} if from_name else {})},
            "to": {"email": to_email, **({"name": to_name} if to_name else {})},
            "subject": subject,
            "template": {
                "template_id": template_id,
                **({"variables": variables} if variables else {}),
            },
        }
        async with self._async_client() as c:
            return self._handle_response(await c.post("/v1/emails/template", json=body))

    async def asend_email(
        self,
        *,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        markdown_content: str | None = None,
        html_content: str | None = None,
        text_content: str | None = None,
    ) -> dict[str, Any]:
        email_obj: dict[str, Any] = {
            "from": {"email": from_email, **({"name": from_name} if from_name else {})},
            "to": [{"email": to_email, **({"name": to_name} if to_name else {})}],
            "subject": subject,
        }
        if markdown_content:
            email_obj["markdown_content"] = markdown_content
        elif html_content:
            email_obj["html_content"] = html_content
        elif text_content:
            email_obj["text_content"] = text_content
        async with self._async_client() as c:
            return self._handle_response(
                await c.post("/v1/emails/send", json={"emails": [email_obj]})
            )

    async def arequest_consent(
        self,
        *,
        domain: str,
        emails: list[str],
    ) -> dict[str, Any]:
        async with self._async_client() as c:
            return self._handle_response(
                await c.post("/v1/emails/consent", json={"domain": domain, "emails": emails})
            )

    async def acheck_consent(self, email: str) -> list[dict[str, Any]]:
        async with self._async_client() as c:
            return self._handle_response(await c.get(f"/v1/emails/{email}"))
