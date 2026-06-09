# langchain-goodsender

LangChain tools for [GoodSender](https://goodsender.com) — the free transactional email API with built-in consent management. Send OTP codes, MFA enrollment, new-device alerts, order confirmations, and more via predefined templates. Send custom/marketing email to recipients who have granted consent via the Permission Loop.

## Install

```bash
pip install langchain-goodsender
```

## Authentication

Set your API key as an environment variable:

```bash
export GOODSENDER_API_KEY="gs_..."
```

Or pass it directly:

```python
from langchain_goodsender import GoodSenderToolkit

toolkit = GoodSenderToolkit(api_key="gs_...")
```

Get a free API key at [goodsender.com](https://goodsender.com) — 100,000 emails/month free, no credit card required.

## Quick start

```python
from langchain_goodsender import GoodSenderToolkit
from langchain_openai import ChatOpenAI

toolkit = GoodSenderToolkit()  # reads GOODSENDER_API_KEY
tools = toolkit.get_tools()

model = ChatOpenAI(model="gpt-4o").bind_tools(tools)
result = model.invoke("Send an OTP code 482193 to alice@example.com from noreply@myapp.com with app_name MyApp")
```

## Tools

### `goodsender_send_template`

Send a predefined transactional email **instantly** to any address — **no recipient consent needed**.

Available `template_id` values: `mfa_enrollment`, `new_device_login`, `order_completed`, `otp_code`, `email_changed`, `password_changed`, `order_receipt`.

### `goodsender_send_email`

Send a custom email (markdown, HTML, or plain text).

> **Consent caveat:** This endpoint is **consent-gated**. The recipient must have approved via the GoodSender Permission Loop before the email delivers. If the recipient has not granted consent, the send is silently filtered — the email is **not** delivered. Use `goodsender_request_consent` first.

### `goodsender_request_consent`

Ask one or more recipients to approve future custom/marketing email from your sending domain. GoodSender sends each recipient a consent request. Once they click approve, their status becomes `granted` and custom sends will deliver instantly.

## Consent caveat

GoodSender has two sending paths:

| Path | Endpoint | Consent required? |
|------|----------|-------------------|
| **Transactional templates** | `goodsender_send_template` | No — delivers instantly to any address |
| **Custom/marketing email** | `goodsender_send_email` | **Yes** — recipient must have granted consent |

If your agent needs to send a custom email to a new recipient, it must first call `goodsender_request_consent` and wait for the recipient to approve. Transactional templates (`otp_code`, `mfa_enrollment`, etc.) bypass this entirely.

## Template variables

Each template accepts optional string variables. All default to empty if omitted.

| `template_id` | Variables |
|---|---|
| `otp_code` | `app_name`, `otp_code`, `expiry_minutes`, `purpose`, `anti_phishing_notice` |
| `mfa_enrollment` | `app_name`, `mfa_method`, `enrolled_at` |
| `new_device_login` | `app_name`, `login_time`, `additional_info` |
| `order_completed` | `app_name`, `order_id`, `order_total`, `completed_at` |
| `order_receipt` | `app_name`, `description`, `total`, `purchase_date`, `receipt_number`, `payment_method` |
| `email_changed` | `app_name`, `new_email`, `changed_at`, `additional_info` |
| `password_changed` | `app_name`, `changed_at`, `additional_info` |


## API Reference

Full docs: [goodsender.com/docs/api-reference](https://goodsender.com/docs/api-reference)

## License

MIT
