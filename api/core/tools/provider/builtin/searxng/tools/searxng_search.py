import json
import re
from typing import Any

import requests

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class SearXNGSearchResults(dict):
    """Wrapper for search results."""

    def __init__(self, data: str):
        super().__init__(json.loads(data))
        self.__dict__ = self

    @property
    def results(self) -> Any:
        return self.get("results", [])


class SearXNGSearchTool(BuiltinTool):
    """
    Tool for performing a search using SearXNG engine.
    """

    # the type of Items that we are searching for
    SEARCH_TYPE: dict[str, str] = {
        "page": "general",
        "news": "news",
        "image": "images",
        "video": "videos",
        "file": "files",
        "map": "maps",
        "music": "music",
        "code": "it",
        "science": "science",
        "patent": "patents",
        # "social": "social",
        # "code": "code",
        "dictionary": "dictionary",
        # "wikidata": "wikidata",
        # "torrent": "torrent",
        # "reddit": "reddit",
        # "github": "github",
        # "wikipedia": "wikipedia",
    }
    LINK_FILED: dict[str, str] = {
        "page": "url",
        "news": "url",
        "image": "img_src",
        "video": "iframe_src",
        "file": "magnetlink",
    }
    TEXT_FILED: dict[str, str] = {
        "page": "content",
        "news": "content",
        "image": "img_src",
        "video": "iframe_src",
        "file": "magnetlink"
    }
    ## https://docs.searxng.org/user/configured_engines.html
    RESULT_TYPE_BANGS: dict[str, str] = {
        "json": "json_txt",
        "text": "text",
        "link": "link",
        "object": "objects"
    }

    def _invoke_query(self, user_id: str, host: str, query: str, search_type: str, result_type: str, topK: int = 5) -> list[dict]:
        """Run query and return the results."""

        search_type = search_type.lower()
        if search_type not in self.SEARCH_TYPE.keys():
            search_type= "page"
        categories = self.SEARCH_TYPE[search_type]

        done=False
        for tag, bang in self.SEARCH_TYPE.items():
            tgts = [f"!{bang}"]
            if bang.endswith('s'):
                tgts.append(f"!{bang[:-1]}")
            if not bang.endswith('s'):
                tgts.append(f"!{bang}s")
            print(f'!!search_type bang={bang} tgts={tgts}')
            for tgt in tgts:
                if tgt in query:
                    categories = bang
                    query = query.replace(tgt, "")
                    done=True
                    break
            if done:
                break

        for bang, res in self.RESULT_TYPE_BANGS.items():
            if f"!{res}" in query:
                result_type = res
                query = query.replace(f"!{res}", "")
                break

        # find regex like "!n=12"
        m = re.search(r"!n=(\d+)", query)
        if m:
            topK = int(m.group(1))
            query = query.replace(m.group(0), "")
        
        query = query.replace("  ", " ").strip()

        response = requests.get(host, params={
            "q": query, 
            "format": "json", 
            "categories": categories,
        })

        if response.status_code != 200:
            raise Exception(f'Error {response.status_code}: {response.text}')
        
        search_results = SearXNGSearchResults(response.text).results[:topK]
        print(f'!!search_results nbr={len(search_results)}')
        results = []

        if result_type == 'objects':
            # transform dic to json string
            for i, obj in enumerate(search_results):
                print(f'!!object answer #{i+1}')
                for tag in ['image', 'video', 'file']:
                    fld = self.LINK_FILED[tag]
                    ref = obj.get(fld)
                    if ref:
                        print(f'!! -> the answer includes a {tag}({fld}) : "{ref}"')
                        # ref="http://hdqwalls.com/wallpapers/eiffel-tower-in-paris-t1.jpg"
                        obj[f'_{tag}'] = f"{fld}:{ref}"
                obj[f'_answer_no'] = i+1
                results.append(self.create_json_message(obj))

        elif result_type == 'json_txt':
            # transform dic to json string
            results = [ self.create_text_message(text=json.dumps(dic, indent=4)) for dic in search_results ]

        elif result_type == 'link':
            if search_type == "page" or search_type == "news":
                for r in search_results:
                    results.append(self.create_text_message(
                        text=f'{r["title"]}: {r.get(self.LINK_FILED[search_type], "")}'
                    ))
            elif search_type == "image":
                for r in search_results:
                    results.append(self.create_image_message(
                        image=r.get(self.LINK_FILED[search_type], "")
                    ))
            else:
                for r in search_results:
                    results.append(self.create_link_message(
                        link=r.get(self.LINK_FILED[search_type], "")
                    ))

        else:
            text = ''
            for i, r in enumerate(search_results):
                text += f'{i+1}: {r["title"]} - {r.get(self.TEXT_FILED[search_type], "")}\n'

            results = [ self.create_text_message(text=self.summary(user_id=user_id, content=text)) ]

        print(f"\n!!SearXNG._invoke_query: nbr={len(results)}")
        return results, {'search_type': categories, 'result_type': result_type, 'query': query, 'topK': topK }
        


    def _invoke(self, user_id: str, tool_parameters: dict[str, Any]) -> ToolInvokeMessage | list[ToolInvokeMessage]:
        """
        Invoke the SearXNG search tool.

        Args:
            user_id (str): The ID of the user invoking the tool.
            tool_parameters (dict[str, Any]): The parameters for the tool invocation.

        Returns:
            ToolInvokeMessage | list[ToolInvokeMessage]: The result of the tool invocation.
        """

        host = self.runtime.credentials.get('searxng_base_url', None)
        if not host:
            raise Exception('SearXNG api is required')
                
        query = tool_parameters.get('query')
        if not query:
            return self.create_text_message('Please input query')
                
        num_results = min(tool_parameters.get('num_results', 5), 50)
        search_type = tool_parameters.get('search_type') or 'page'
        result_type = tool_parameters.get('result_type') or 'text'

        return self._invoke_query(
            user_id=user_id, 
            host=host, 
            query=query, 
            search_type=search_type, 
            result_type=result_type, 
            topK=num_results
        )
