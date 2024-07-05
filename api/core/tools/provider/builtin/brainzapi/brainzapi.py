from typing import Any

from core.tools.errors import ToolProviderCredentialValidationError
from core.tools.provider.builtin.searchapi.tools.google import GoogleTool
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController


class BrainzAPIProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        return
