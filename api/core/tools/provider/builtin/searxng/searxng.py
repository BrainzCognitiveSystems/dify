from typing import Any

from core.tools.errors import ToolProviderCredentialValidationError
from core.tools.provider.builtin.searxng.tools.searxng_search import SearXNGSearchTool
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController


class SearXNGProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        print(f"\n!!!  SearXNGProvider._validate_credentials (1): {credentials}")
        return # DG shortcircuit !!!
        try:
            tool = SearXNGSearchTool().fork_tool_runtime(
                runtime={
                    "credentials": credentials,
                }
            )
            print(f"\n!!!  SearXNGProvider._validate_credentials (2): tool={tool}")
            tool.invoke(
                user_id='',
                tool_parameters={
                    "query": "SearXNG",
                    "limit": 1,
                    "search_type": "page",
                    "result_type": "link"
                },
            )
        except Exception as e:
            print(f"\n!!!  SearXNGProvider._validate_credentials (3): error {e}")
            raise ToolProviderCredentialValidationError(str(e))
