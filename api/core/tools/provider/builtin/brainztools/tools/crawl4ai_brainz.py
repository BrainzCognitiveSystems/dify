from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

import logging
logger = logging.getLogger(__name__)

# Doc: https://crawl4ai.com/mkdocs/
# class CrawlResult(BaseModel):
#     url: str
#     html: str
#     success: bool
#     cleaned_html: Optional[str] = None
#     media: Dict[str, List[Dict]] = {}
#     links: Dict[str, List[Dict]] = {}
#     screenshot: Optional[str] = None
#     markdown: Optional[str] = None
#     extracted_content: Optional[str] = None
#     metadata: Optional[dict] = None
#     error_message: Optional[str] = None

import requests
import json
import base64

url = "https://www.nbcnews.com/business"
url = "https://dify.ai/"
url = "https://en.wikipedia.org/wiki/Zinc%E2%80%93air_battery"


"""
curl -X POST -H "Content-Type: application/json" -d '{
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "include_raw_html": true,
  "word_count_threshold": 10,
  "extraction_strategy": "NoExtractionStrategy",
  "chunking_strategy": "RegexChunking",
  "screenshot": true
}' https://crawl4ai.com/crawl
"""

class Crawl4AI_BrainzTools(BuiltinTool):

    @classmethod
    def get_results(cls, urls: list[str], options=None):
        # Options: 
        options = { 'word_count_threshold': 10, 'bypass_cache':True, 'screenshot':False }
        # js=js_code , css='p'
        screenshot_save=True

        data = {
            "urls": urls,
            "include_raw_html": True,
            "word_count_threshold": 10,
            "extraction_strategy": "NoExtractionStrategy",
            "chunking_strategy": "RegexChunking",
            "screenshot": True,
        }
        crawl4ai_endpoint = "https://crawl4ai.com/crawl"
        crawl4ai_endpoint = "http://localhost:8098/crawl"

        # See: GUI Old Interface : http://localhost:8098/old

        response = requests.post(crawl4ai_endpoint, json=data)
        results = {}
        try:
            answer = response.content.decode('utf-8')
            json_response = json.loads(answer)
            results_ = json_response['results']
            for i, result in enumerate(results_):
                #  txt = json.dumps(result, indent=4)
                try:
                    extracted_content=result.get('extracted_content',"[]")
                    result['extracted_content'] = json.loads(extracted_content)
                    # from : JPG img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    img_base64 = result['screenshot']
                    base64_img_bytes = img_base64.encode('utf-8')
                    decoded_image_data = base64.decodebytes(base64_img_bytes)
                    if screenshot_save:
                        result['screenshot_filename'] = f'screenshot-{i+1:03d}.jpg'
                        with open(result['screenshot_filename'], 'wb') as file_to_save:
                            file_to_save.write(decoded_image_data)
                        result.pop('screenshot')
                except:
                    pass
                # print(txt)
                results[url] = result
            # {
            #     'success':result.get('success','?'),
            #     'error_message':results.get('error_message',""),
            #     'html':result.get('html',""),
            #     'cleaned_html':result.get('cleaned_html',""),
            #     'screenshot':result.get('screenshot',""),
            #     'markdown':result.get('markdown',""),
            #     'extracted_content': result.get('extracted_content',""),
            #     'metadata': result.get('metadata',{}),
            #     'links': result.get('links',{}),
            #     'media': result.get('media',{}),
            # }
        except Exception as e:
            print(f'Error: {e}')

        # Run the crawler on a list of URLs
        return results

    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        urls = (tool_parameters.get('url') or "").split('|')
        options = tool_parameters.get('options', "")
        results = self.get_results(urls, options)
        results = [ self.create_json_message(obj) for obj in results.values() ]
        meta = {
            "engine": "carawl4ai_brainz",
            "url": urls,
            "options": options,
            "tool_parameters": tool_parameters,
        }
        meta['results_nbr'] = len(results)
        return results, meta


if __name__ == "__main__":
    urls = ["https://www.nbcnews.com/business", "https://www.nbcnews.com/"]
    options = { 'word_count_threshold': 10, 'bypass_cache':True, 'screenshot':False }
    results = Crawl4AI_BrainzTools.get_results(urls, options)
    print(results)
