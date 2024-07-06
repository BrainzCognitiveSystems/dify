from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.errors import ToolInvokeError
from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.utils.web_reader_tool import dict_full_template


class WebscraperTool_BrainzTools(BuiltinTool):
    def _invoke(self,
                user_id: str,
                tool_parameters: dict[str, Any],
                ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
            invoke tools
        """
        try:
            url = tool_parameters.get('url', '')
            user_agent = tool_parameters.get('user_agent', '')
            if not url:
                return self.create_text_message('Please input url')

            # get webpage
            result = self.get_url_dict(url, user_agent)

            if tool_parameters.get('generate_summary'):
                # summarize and return
                text = dict_full_template(result)
                summary = self.summary(user_id=user_id, content=text)
                result['summary'] = summary
                summarize = self.do_summarize(user_id, text)
                result['summarize'] = {
                    'content':summarize.message.content,
                    'model':summarize.model,
                    'prompt_tokens':summarize.usage.prompt_tokens,
                    'completion_tokens':summarize.usage.completion_tokens,
                    }

            res = self.create_json_message(result)
            return res
        
        except Exception as e:
            raise ToolInvokeError(str(e))
