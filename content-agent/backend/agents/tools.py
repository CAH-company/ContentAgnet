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

    def _run(self, query: str) -> str:
        results = search_documents(query, n_results=5)
        if not results:
            return "Brak relevantnych dokumentów w bazie wiedzy."
        return "\n\n---\n\n".join(results)


rag_search_tool = RagSearchTool()
