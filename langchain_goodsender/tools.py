"""LangChain tools for the GoodSender email API."""

from __future__ import annotations

from typing import Any, Optional, Type

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from langchain_goodsender.client import GoodSenderClient, TEMPLATE_IDS

_TEMPLATE_LIST = ", ".join(f"`{t}`" for t in TEMPLATE_IDS)


# ---------------------------------------------------------------------------
# Pydantic v2 args schemas
# ---------------------------------------------------------------------------


class SendTemplateInput(BaseModel):
    """Input for sending a transactional template email via GoodSender."""

    template_id: str = Field(
        description=(
            "Predefined transactional template identifier. "
            f"Available values: {_TEMPLATE_LIST}."
        ),
    )
    to_email: str = Field(description="Recipient email address.")
    subject: str = Field(description="Email subject line.")
    from_email: str = Field(description="Sender email address (must be on an authenticated domain).")
    from_name: Optional[str] = Field(default=None, description="Sender display name.")
    to_name: Optional[str] = Field(default=None, description="Recipient display name.")
    variables: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Key-value pairs to fill template placeholders "
            "(e.g. app_name, otp_code, expiry_minutes). All are optional."
        ),
    )


class SendEmailInput(BaseModel):
    """Input for sending a custom/marketing email via GoodSender."""

    to_email: str = Field(description="Recipient email address.")
    subject: str = Field(description="Email subject line.")
    from_email: str = Field(description="Sender email address (must be on an authenticated domain).")
    from_name: Optional[str] = Field(default=None, description="Sender display name.")
    to_name: Optional[str] = Field(default=None, description="Recipient display name.")
    markdown_content: Optional[str] = Field(
        default=None,
        description="Markdown email body (auto-converted to bulletproof HTML).",
    )
    html_content: Optional[str] = Field(default=None, description="HTML email body.")
    text_content: Optional[str] = Field(default=None, description="Plain-text email body.")


class RequestConsentInput(BaseModel):
    """Input for requesting recipient consent for marketing emails."""

    domain: str = Field(description="Your sending domain (e.g. 'example.com').")
    emails: list[str] = Field(
        description="One or more recipient email addresses to request consent from (max 1000).",
    )


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


class GoodSenderSendTemplateTool(BaseTool):
    """Send a predefined transactional email instantly — no recipient consent needed.

    Uses the GoodSender template endpoint (POST /v1/emails/template).
    Transactional templates deliver to *any* recipient address regardless of
    consent status. Available template_id values: mfa_enrollment,
    new_device_login, order_completed, otp_code, email_changed,
    password_changed, order_receipt. The catalog grows over time.
    """

    name: str = "goodsender_send_template"
    description: str = (
        "Send a predefined transactional email instantly to any address — "
        "no recipient consent needed. Available template_id values: "
        f"{_TEMPLATE_LIST}. "
        "Pass template variables (app_name, otp_code, expiry_minutes, etc.) to "
        "personalise the message. Use this for OTP codes, MFA enrollment, "
        "new-device alerts, password/email change confirmations, order "
        "completed, and order receipt notifications."
    )
    args_schema: Type[BaseModel] = SendTemplateInput
    client: GoodSenderClient = Field(exclude=True)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        template_id: str,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        variables: dict[str, str] | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        result = self.client.send_template(
            template_id=template_id,
            to_email=to_email,
            subject=subject,
            from_email=from_email,
            from_name=from_name,
            to_name=to_name,
            variables=variables,
        )
        return f"Template '{template_id}' sent to {to_email}. Status: {result.get('status', 'unknown')}"

    async def _arun(
        self,
        template_id: str,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        variables: dict[str, str] | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        result = await self.client.asend_template(
            template_id=template_id,
            to_email=to_email,
            subject=subject,
            from_email=from_email,
            from_name=from_name,
            to_name=to_name,
            variables=variables,
        )
        return f"Template '{template_id}' sent to {to_email}. Status: {result.get('status', 'unknown')}"


class GoodSenderSendEmailTool(BaseTool):
    """Send a custom/marketing email (consent-gated — NOT guaranteed to deliver immediately).

    Uses the GoodSender send endpoint (POST /v1/emails/send). This endpoint
    is consent-gated: the recipient must have previously approved via the
    Permission Loop. If the recipient has not granted consent, the email will
    be filtered out and NOT delivered. Use goodsender_request_consent first if
    the recipient hasn't approved yet.

    Supports markdown (auto-converted to HTML), raw HTML, and plain text.
    """

    name: str = "goodsender_send_email"
    description: str = (
        "Send a custom/marketing email to a recipient. "
        "WARNING: This is consent-gated — the recipient MUST have approved "
        "via the GoodSender Permission Loop before delivery succeeds. If the "
        "recipient has not granted consent, the email is silently filtered "
        "and NOT delivered. Use goodsender_request_consent first to ask for "
        "consent. Supports markdown_content (auto-converted to HTML), "
        "html_content, or text_content."
    )
    args_schema: Type[BaseModel] = SendEmailInput
    client: GoodSenderClient = Field(exclude=True)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        markdown_content: str | None = None,
        html_content: str | None = None,
        text_content: str | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        result = self.client.send_email(
            to_email=to_email,
            subject=subject,
            from_email=from_email,
            from_name=from_name,
            to_name=to_name,
            markdown_content=markdown_content,
            html_content=html_content,
            text_content=text_content,
        )
        sent = result.get("sent", 0)
        declined = result.get("declined", 0)
        return (
            f"Email to {to_email}: {sent} sent, {declined} declined "
            f"(declined means consent not granted)."
        )

    async def _arun(
        self,
        to_email: str,
        subject: str,
        from_email: str,
        from_name: str | None = None,
        to_name: str | None = None,
        markdown_content: str | None = None,
        html_content: str | None = None,
        text_content: str | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        result = await self.client.asend_email(
            to_email=to_email,
            subject=subject,
            from_email=from_email,
            from_name=from_name,
            to_name=to_name,
            markdown_content=markdown_content,
            html_content=html_content,
            text_content=text_content,
        )
        sent = result.get("sent", 0)
        declined = result.get("declined", 0)
        return (
            f"Email to {to_email}: {sent} sent, {declined} declined "
            f"(declined means consent not granted)."
        )


class GoodSenderRequestConsentTool(BaseTool):
    """Request consent from recipients to receive marketing/custom emails.

    Uses the GoodSender consent endpoint (POST /v1/emails/consent).
    This sends a consent-request email to each specified address. The
    recipient must click approve before custom sends to them will deliver.
    Consent is stored per sender-domain / recipient pair.
    """

    name: str = "goodsender_request_consent"
    description: str = (
        "Ask one or more recipients to approve future custom/marketing email "
        "from your sending domain. GoodSender sends each recipient a consent "
        "request. Once a recipient clicks approve, their status "
        "becomes 'granted' and custom sends to them will deliver instantly. "
        "Required before goodsender_send_email will deliver to a recipient."
    )
    args_schema: Type[BaseModel] = RequestConsentInput
    client: GoodSenderClient = Field(exclude=True)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        domain: str,
        emails: list[str],
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        result = self.client.request_consent(domain=domain, emails=emails)
        items = result.get("emails", [])
        lines = [
            f"  {r['email']}: {r.get('consentStatus', 'unknown')}" for r in items
        ]
        return "Consent requests sent:\n" + "\n".join(lines)

    async def _arun(
        self,
        domain: str,
        emails: list[str],
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        result = await self.client.arequest_consent(domain=domain, emails=emails)
        items = result.get("emails", [])
        lines = [
            f"  {r['email']}: {r.get('consentStatus', 'unknown')}" for r in items
        ]
        return "Consent requests sent:\n" + "\n".join(lines)
