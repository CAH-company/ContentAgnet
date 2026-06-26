import os
import httpx
from crewai.tools import BaseTool
from rag.store import search_documents
from pydantic import BaseModel


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
    user_id: str = ""

    def _run(self, query: str) -> str:
        results = search_documents(query, user_id=self.user_id, n_results=5)
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
        searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
        try:
            resp = httpx.get(
                f"{searxng_url}/search",
                params={"q": query, "format": "json", "language": "pl-PL"},
                timeout=15
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])[:5]
        except Exception as e:
            return f"Błąd wyszukiwania: {e}"

        if not results:
            return "Brak wyników wyszukiwania."

        output = []
        for r in results:
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            output.append(f"**{title}**\n{url}\n{content}")
        return "\n\n---\n\n".join(output)


web_search_tool = WebSearchTool()
