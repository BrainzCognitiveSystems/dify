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
    CATEGORY_ALIASES: dict[str, str] = {
        "image": "images",
        "picts": "images",
        "picture": "images",
        "pictures": "images",
        "video": "videos",
        "vidéo": "videos",
        "vidéos": "videos",
        "file": "files",
        "map": "maps",
        "musics": "music",
        "code": "it",
        "arxiv": "science",
        "patent": "patents",
        "dictionary": "dictionary",
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
        categories = self.SEARCH_TYPE.get(search_type, "general")

        bang_to_category = { v: v for k, v in self.SEARCH_TYPE.items()}
        for bang, category in self.CATEGORY_ALIASES.items():
            bang_to_category[bang] = category

        for bang, category in bang_to_category.items():
            tgt = f"!{bang}"
            if tgt in query:
                categories = category
                query = query.replace(tgt, category)
                break
        print(f'!!categories={categories}')

        for bang, res in self.RESULT_TYPE_BANGS.items():
            if f"!{res}" in query:
                result_type = res
                query = query.replace(f"!{res}", "")
                break
        print(f'!!result_type={result_type}')

        # find regex like "!n=12"
        m = re.search(r"!n=(\d+)", query)
        if m:
            topK = int(m.group(1))
            query = query.replace(m.group(0), "")
        
        params={
            "format": "json", 
            "categories": categories,
        }


        # time_range=[day, week, month, year]
        # find regex like "!tr=day"
        m = re.search(r"!(?:time_range|tr)=(day|week|month|year)", query)
        if m:
            params["time_range"] = m.group(1)
            query = query.replace(m.group(0), "")

        # language=[fr, en, es, ...]
        # find regex like "!lang=fr"
        m = re.search(r"!(?:language|lang|lg)=(\w+)", query)
        if m:
            params["language"] = m.group(1)
            query = query.replace(m.group(0), "")

        # mandatory_fields=[title, url, content, publishedDate...]
        # find regex like "!mf=title,url"
        m = re.search(r"!(?:mandatory_fields|mf)=(\w+(?:,\w+)*)", query)
        if m:
            params["mandatory_fields"] = m.group(1)
            query = query.replace(m.group(0), "")

        params_internal={}
        # sortBy=[relevance, date]
        # find regex like "!sort=relevance"
        m = re.search(r"!(?:sort|sortBy)=(relevance|date)", query)
        if m:
            params_internal["sortBy"] = m.group(1)
            query = query.replace(m.group(0), "")

        query = query.replace("  ", " ").strip()
        params["q"] = query

        response = requests.get(host, params=params)

        if response.status_code != 200:
            raise Exception(f'Error {response.status_code}: {response.text}')
        
        search_results = SearXNGSearchResults(response.text).results
        results_nbr = len(search_results)
        print(f'!!search_results nbr={results_nbr}')

        if True or "date" in params_internal.get("sortBy","").lower():
            # search_results = sorted(search_results, key=lambda x: x.get("publishedDate", "0000-00-00T00:00:00Z"), reverse=True)
            pass

        # search_results = search_results[:topK]

        for sr in search_results:
            try:
                tgt = "http://dx.doi.org/https://doi.org/1"
                if sr['url'].startswith(tgt):
                    sr['url'] = sr['url'].replace(tgt, "https://doi.org/")
            except: pass
            try:
                s = sr["publishedDate"].replace('T',' ').split(' ',1) # ex: "2024-06-21T12:20:00.736459Zxxxxx",
                if len(s)==1:
                    sr["publishedDate_h"] = s[0]
                else:
                    s1 = s[1][:8]
                    if s1=="00:00:00":
                        sr["publishedDate_h"] = s[0]
                    else:
                        sr["publishedDate_h"] = s[0] + " " + s1
            except: pass

        results = []

        if result_type == 'objects':
            # transform dic to json string
            for i, obj in enumerate(search_results):
                print(f'!!object answer #{i+1}')
                if "publisheddate" in params.get("mandatory_fields","").lower():
                    if not obj.get("publishedDate"):
                        continue
                for tag in ['image', 'video', 'file']:
                    fld = self.LINK_FILED[tag]
                    ref = obj.get(fld)
                    if ref:
                        print(f'!! -> the answer includes a {tag}({fld}) : "{ref}"')
                        # ref="http://hdqwalls.com/wallpapers/eiffel-tower-in-paris-t1.jpg"
                        obj[f'_{tag}'] = f"{fld}:{ref}"
                obj[f'_answer_no'] = i+1
                results.append(self.create_json_message(obj))
                if len(results) >= topK:
                    break

        elif result_type == 'json_txt':
            # transform dic to json string
            results = [ self.create_text_message(text=json.dumps(dic, indent=4)) for dic in search_results ]

        elif result_type == 'link':
            search_results = search_results[:topK]
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
            search_results = search_results[:topK]
            text = ''
            for i, r in enumerate(search_results):
                text += f'{i+1}: {r["title"]} - {r.get(self.TEXT_FILED[search_type], "")}\n'

            results = [ self.create_text_message(text=self.summary(user_id=user_id, content=text)) ]

        print(f"\n!!SearXNG._invoke_query: nbr={len(results)}")
        return results, {'search_type': categories, 'result_type': result_type, 'query': query, 'topK': topK,
                         'results_nbr':results_nbr, "language":params.get("language",""), "time_range":params.get("time_range","") }
        


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
