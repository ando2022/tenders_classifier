import json
import urllib.parse
import urllib.request
from typing import Any

from . import base


def wikipedia_search(query: str) -> dict[str, Any]:
    """Search Wikipedia and return relevant article summaries."""
    try:
        # First, search for relevant articles
        search_results = _search_wikipedia_articles(query)
        if not search_results:
            return {"error": "No articles found for query"}
        
        # Get the top article's summary
        top_article = search_results[0]
        summary = _get_article_summary(top_article['title'])
        
        return {
            "title": top_article['title'],
            "summary": summary,
            "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(top_article['title'].replace(' ', '_'))}",
            "search_results": [{"title": r['title'], "snippet": r.get('snippet', '')} for r in search_results[:3]]
        }
    except Exception as e:
        return {"error": f"Wikipedia search failed: {str(e)}"}


def _search_wikipedia_articles(query: str) -> list[dict]:
    """Search for Wikipedia articles matching the query."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={encoded_query}&srlimit=5"
    
    request = urllib.request.Request(url)
    request.add_header('User-Agent', 'Romeo-Agent/1.0 (https://github.com/example/romeo-agent)')
    
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data.get('query', {}).get('search', [])


def _get_article_summary(title: str) -> str:
    """Get the summary/extract of a Wikipedia article."""
    encoded_title = urllib.parse.quote(title)
    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=true&explaintext=true&titles={encoded_title}"
    
    request = urllib.request.Request(url)
    request.add_header('User-Agent', 'Romeo-Agent/1.0 (https://github.com/example/romeo-agent)')
    
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
        pages = data.get('query', {}).get('pages', {})
        
        for page in pages.values():
            return page.get('extract', 'No summary available.')
        
        return 'No summary available.'


class WikiTool(base.Tool):
    name = "wiki"

    def schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Search Wikipedia for articles and get the most relevant summary with search results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to search for on Wikipedia"}
                    },
                    "required": ["query"],
                },
            },
        }

    def run(self, kwargs):
        query = kwargs["query"]
        print(f"[WIKI] Searching for `{query}`...")
        result = wikipedia_search(query)
        print(f"[WIKI] Result:\n{json.dumps(result, indent=2)}")
        return result
