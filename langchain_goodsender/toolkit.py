"""GoodSenderToolkit — groups the GoodSender LangChain tools."""

from __future__ import annotations

from typing import List

from langchain_core.tools import BaseTool
from pydantic import Field

from langchain_goodsender.client import GoodSenderClient
from langchain_goodsender.tools import (
    GoodSenderRequestConsentTool,
    GoodSenderSendEmailTool,
    GoodSenderSendTemplateTool,
)


class GoodSenderToolkit:
    """Convenience wrapper that creates a shared client and returns all tools.

    Usage::

        from langchain_goodsender import GoodSenderToolkit

        toolkit = GoodSenderToolkit(api_key="gs_...")   # or set GOODSENDER_API_KEY
        tools = toolkit.get_tools()
        # bind to a model: model.bind_tools(tools)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.goodsender.com",
        timeout: float = 30.0,
    ) -> None:
        self.client = GoodSenderClient(
            api_key=api_key, base_url=base_url, timeout=timeout
        )

    def get_tools(self) -> List[BaseTool]:
        """Return the three GoodSender tools backed by a shared client."""
        return [
            GoodSenderSendTemplateTool(client=self.client),
            GoodSenderSendEmailTool(client=self.client),
            GoodSenderRequestConsentTool(client=self.client),
        ]
