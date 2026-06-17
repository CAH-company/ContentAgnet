from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from .tools import rag_search_tool
import os


class ContentMarketingCrew:

    def __init__(self):
        self.llm = "claude-sonnet-4-5"
        self.search_tool = SerperDevTool()

    def run(self, context: dict) -> dict:
        topic = context["topic"]
        platform = context["platform"]
        post_type = context["post_type"]
        is_revision = "revision_comment" in context

        revision_note = ""
        if is_revision:
            revision_note = f"""
            POPRZEDNIA WERSJA:
            {context.get('previous_result', '')}

            KOMENTARZ DO POPRAWKI:
            {context.get('revision_comment', '')}

            Uwzględnij powyższe uwagi w nowej wersji.
            """

        researcher = Agent(
            role="Senior Content Researcher",
            goal=f"Zbadaj temat '{topic}' i znajdź najlepsze kąty narracyjne, "
                 f"aktualne trendy i dane które warto wykorzystać",
            backstory="Jesteś doświadczonym researcherem content marketingu. "
                      "Zawsze szukasz unikalnych perspektyw i aktualnych danych. "
                      "Znasz markę firmy i jej styl komunikacji z dokumentów.",
            tools=[self.search_tool, rag_search_tool],
            llm=self.llm,
            verbose=True
        )

        writer = Agent(
            role="Expert Content Writer",
            goal=f"Napisz angażujący {post_type} na platformę {platform} "
                 f"na podstawie dostarczonego researchu, zgodny z brand voice firmy",
            backstory="Jesteś ekspertem w pisaniu content marketingowego. "
                      "Piszesz w stylu marki, angażująco i naturalnie. "
                      "Zawsze używasz brand voice i przykładowych postów z dokumentów.",
            tools=[rag_search_tool],
            llm=self.llm,
            verbose=True
        )

        editor = Agent(
            role="Content Editor & SEO Specialist",
            goal="Sprawdź i popraw tekst pod kątem jakości, tonu marki, "
                 "SEO i dopasowania do platformy",
            backstory="Jesteś skrupulatnym redaktorem z doświadczeniem w SEO. "
                      "Sprawdzasz czy post brzmi naturalnie, jest zgodny z brand voice "
                      "i zoptymalizowany pod daną platformę.",
            tools=[rag_search_tool],
            llm=self.llm,
            verbose=True
        )

        publisher = Agent(
            role="Content Publisher",
            goal="Sformatuj finalny post gotowy do publikacji, "
                 "dodaj odpowiednie hashtagi i meta-informacje",
            backstory="Formatujesz content idealnie pod każdą platformę. "
                      "Wiesz że LinkedIn lubi dłuższe posty z formatowaniem, "
                      "Twitter/X wymaga zwięzłości, WordPress potrzebuje H2/H3.",
            tools=[],
            llm=self.llm,
            verbose=True
        )

        research_task = Task(
            description=f"""
            Zbadaj temat: "{topic}"
            Platforma: {platform}
            Typ contentu: {post_type}

            1. Przeszukaj internet w poszukiwaniu aktualnych trendów i danych
            2. Przeszukaj bazę wiedzy firmy (RAG) po słowach kluczowych z tematu
            3. Wyciągnij brand voice i przykłady postów z RAG
            4. Przygotuj brief dla writera: kluczowe punkty, dane, angle narracyjny

            {revision_note}
            """,
            agent=researcher,
            expected_output="Szczegółowy brief z kluczowymi punktami, "
                           "danymi i proponowanym kątem narracyjnym"
        )

        platform_length_guide = {
            "blog":      "600–1200 słów, struktura H2/H3, akapity 3-4 zdania",
            "linkedin":  "150–300 słów (short_post), 400–700 słów (article/newsletter), 8–12 slajdów (carousel)",
            "twitter":   "max 280 znaków — liczy się każdy znak",
            "facebook":  "100–400 słów, konwersacyjny, jeden wyraźny przekaz",
            "instagram": "max 125 znaków widocznych przed 'więcej' (caption), 5–10 slajdów (carousel)",
        }.get(platform, "dopasuj długość do platformy")

        write_task = Task(
            description=f"""
            Na podstawie briefu od Researchera napisz {post_type} na {platform}.

            Wymagania:
            - Użyj brand voice z dokumentów firmy
            - Wytyczne długości: {platform_length_guide}
            - Zacznij od mocnego hooka
            - Dodaj wyraźne CTA na końcu

            {revision_note}
            """,
            agent=writer,
            expected_output="Gotowy draft posta zgodny z brand voice"
        )

        edit_task = Task(
            description=f"""
            Sprawdź draft od Writera i popraw:
            - Czy ton jest zgodny z brand voice firmy? (sprawdź RAG)
            - Czy nie ma błędów gramatycznych?
            - Czy jest angażujący i naturalny?
            - Czy jest zoptymalizowany SEO (dla WordPress)?
            - Czy CTA jest wyraźne?

            Jeśli coś wymaga poprawki — popraw to sam, nie odsyłaj do Writera.
            """,
            agent=editor,
            expected_output="Poprawiony, gotowy do publikacji post"
        )

        platform_format_guide = {
            "blog":      "Markdown: ## i ### nagłówki, **bold**, listy, na końcu sugestia meta-opisu (max 155 znaków)",
            "linkedin":  "Krótkie akapity oddzielone enterem, emoji dozwolone (z umiarem), 3–5 hashtagów na końcu. Carousel: każdy slajd jako 'Slajd N: [tytuł]\n[treść]'",
            "twitter":   "Maksymalnie 280 znaków łącznie ze spacjami, 2–3 hashtagi wliczone w limit",
            "facebook":  "Naturalny styl, akapity, emoji dozwolone, 0–3 hashtagi opcjonalnie na końcu",
            "instagram": "Caption: pierwsza linijka to hook (widoczna przed 'więcej'), emoji w tekście, 20–30 hashtagów na samym końcu po pustej linii. Carousel: każdy slajd jako 'Slajd N: [tytuł]\n[treść]'",
        }.get(platform, "dopasuj formatowanie do platformy")

        publish_task = Task(
            description=f"""
            Sformatuj finalny post na platformę {platform}:
            {platform_format_guide}

            Zwróć TYLKO gotowy post bez żadnych komentarzy od siebie.
            """,
            agent=publisher,
            expected_output="Sformatowany post gotowy do wklejenia/publikacji"
        )

        crew = Crew(
            agents=[researcher, writer, editor, publisher],
            tasks=[research_task, write_task, edit_task, publish_task],
            process=Process.sequential,
            verbose=True
        )

        token_input = 0
        token_output = 0

        result = crew.kickoff()

        # Obsługa różnych formatów usage_metrics (crewai 0.51+)
        metrics = getattr(crew, 'usage_metrics', None)
        if metrics is not None:
            if isinstance(metrics, dict):
                token_input = metrics.get('prompt_tokens', 0)
                token_output = metrics.get('completion_tokens', 0)
            else:
                token_input = getattr(metrics, 'prompt_tokens', 0) or 0
                token_output = getattr(metrics, 'completion_tokens', 0) or 0

        return {
            "content": str(result),
            "token_input": token_input,
            "token_output": token_output
        }
