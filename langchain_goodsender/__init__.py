"""langchain-goodsender — LangChain tools for the GoodSender email API."""

from langchain_goodsender.client import GoodSenderClient, GoodSenderError, TEMPLATE_IDS
from langchain_goodsender.toolkit import GoodSenderToolkit
from langchain_goodsender.tools import (
    GoodSenderRequestConsentTool,
    GoodSenderSendEmailTool,
    GoodSenderSendTemplateTool,
)

__all__ = [
    "GoodSenderClient",
    "GoodSenderError",
    "GoodSenderRequestConsentTool",
    "GoodSenderSendEmailTool",
    "GoodSenderSendTemplateTool",
    "GoodSenderToolkit",
    "TEMPLATE_IDS",
]
