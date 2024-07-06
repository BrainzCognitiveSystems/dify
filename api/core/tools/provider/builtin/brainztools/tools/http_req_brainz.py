from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

from core.tools.tool.api_tool import ApiTool


class HTTP_Req_BrainzTools(ApiTool):

    def __init__(self, api_bundle: BuiltinTool):
        super().__init__(api_bundle)
        self.api_bundle = api_bundle
        self.api_bundle.method = "POST"
        self.api_bundle.server_url = "https://crawl4ai.com/crawl"
        self.api_bundle.headers = {
            "Content-Type": "application/json"
        }

    def _invokeXXX(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        urls = (tool_parameters.get('url') or "").split('|')
        options = tool_parameters.get('options', "")
        results = self.get_results(urls, options)
        results = [ self.create_json_message(obj) for obj in results.values() ]
        meta = {
            "engine": "carawl4ai_brainz",
            "url": urls,
            "options": options,
            "tool_parameters": tool_parameters,
            'results_nbr': len(results)
        }
        return results, meta
    
    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage | list[ToolInvokeMessage]:
        """
        invoke http request
        """
        # assemble request
        headers = self.assembling_request(tool_parameters)

        # do http request
        response = self.do_http_request(self.api_bundle.server_url, self.api_bundle.method, headers, tool_parameters)

        # validate response
        response = self.validate_and_parse_response(response)

        # assemble invoke message
        return self.create_text_message(response)

