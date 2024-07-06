from typing import Any, Union

if __name__ != "__main__":
    from core.tools.entities.tool_entities import ToolInvokeMessage
    from core.tools.tool.builtin_tool import BuiltinTool
else:
    class BuiltinTool:
        pass

    class ToolInvokeMessage:
        pass

import logging
logger = logging.getLogger(__name__)

from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import NoExtractionStrategy

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



class Crawl4AI_BrainzTools(BuiltinTool):

    @classmethod
    def get_results(cls, urls: list[str], options=None):
        # Options: 
        options = { 'word_count_threshold': 10, 'bypass_cache':True, 'screenshot':False }
        # js=js_code , css='p'

        # Create an instance of WebCrawler
        crawler = WebCrawler(crawler_strategy=NoExtractionStrategy())

        # Warm up the crawler (load necessary models)
        crawler.warmup()

        # Run the crawler on a list of URLs
        results = {}
        for url in urls:
            result = crawler.run(url=url, **options)
            results[url] = {
                'success':results.success,
                'error_message':results.error_message,
                'html':results.html, 'cleaned_html':results.cleaned_html,
                'screenshot':results.screenshot,
                'markdown':results.markdown ,
                'extracted_content': result.extracted_content,
                'metadata': result.metadata,
                'links': result.links,
                'media': result.media
                }
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
