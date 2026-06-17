import os
from crewai.tools import BaseTool
from rag.store import search_documents
from pydantic import BaseModel
from tavily import TavilyClient


class RagSearchInput(BaseModel):
    query: str


class RagSearchTool(BaseTool):
    name: str = "rag_search"
    description: str = (
        "Przeszukaj bazę wiedzy firmy. Używaj gdy potrzebujesz: "
        "brand voice, przykładowych postów, opisu firmy, słów kluczowych, "
        "lub jakichkolwiek dokumentów wgranych przez użytkownika. "
        "Zawsze wywołaj to narzędzie na początku pracy."
    )
    args_schema: type[BaseModel] = RagSearchInput

    def _run(self, query: str) -> str:
        results = search_documents(query, n_results=5)
        if not results:
            return "Brak relevantnych dokumentów w bazie wiedzy."
        return "\n\n---\n\n".join(results)


class WebSearchInput(BaseModel):
    query: str


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Przeszukaj internet w poszukiwaniu aktualnych informacji, trendów i danych. "
        "Używaj do researchu tematu przed pisaniem contentu."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(query, max_results=5, search_depth="basic")
        results = response.get("results", [])
        if not results:
            return "Brak wyników wyszukiwania."
        output = []
        for r in results:
            output.append(f"**{r['title']}**\n{r['url']}\n{r['content']}")
        return "\n\n---\n\n".join(output)


rag_search_tool = RagSearchTool()
web_search_tool = WebSearchTool()
