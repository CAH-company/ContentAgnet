import os
from dotenv import load_dotenv
from db.supabase_client import supabase
from agents.crew import ContentMarketingCrew

load_dotenv()


def _friendly_error(exc: Exception) -> str:
    msg = str(exc).lower()

    if any(w in msg for w in ["credit", "billing", "payment", "insufficient_quota", "insufficient funds"]):
        return (
            "Brak środków na koncie AI. Skontaktuj się z administratorem "
            "lub odczekaj do jutra — konto może mieć dzienny limit."
        )

    if any(w in msg for w in ["rate limit", "rate_limit", "too many requests", "429"]):
        return "Przekroczono limit zapytań do AI. Odczekaj kilka minut i spróbuj ponownie."

    if any(w in msg for w in ["timeout", "timed out", "read timeout"]):
        return "Agent zbyt długo czekał na odpowiedź — sieć lub serwis AI nie odpowiedział. Spróbuj ponownie."

    if any(w in msg for w in ["connection", "network", "unreachable"]):
        return "Błąd połączenia z serwisem AI. Sprawdź połączenie sieciowe serwera i spróbuj ponownie."

    if any(w in msg for w in ["authentication", "invalid api key", "api key"]):
        return "Błąd klucza API — skontaktuj się z administratorem."

    # Ogólny błąd — nie ujawniaj szczegółów technicznych użytkownikowi
    return "Wystąpił błąd podczas generowania posta. Spróbuj ponownie lub skontaktuj się z administratorem."


def run_agent_task(task_id: str, user_id: str, revision: bool = False):
    try:
        task = supabase.table("tasks").select("*")\
            .eq("id", task_id).single().execute().data

        if not task:
            return

        supabase.table("tasks").update({"status": "running"})\
            .eq("id", task_id).execute()

        context = {
            "topic": task["topic"],
            "platform": task["platform"],
            "post_type": task["post_type"],
            "iteration": task["iteration"],
        }

        if revision and task.get("user_comment"):
            context["previous_result"] = task["result"]
            context["revision_comment"] = task["user_comment"]

        crew = ContentMarketingCrew(user_id=user_id)
        result = crew.run(context)

        supabase.table("tasks").update({
            "status": "review",
            "result": result["content"],
            "token_input": result["token_input"],
            "token_output": result["token_output"],
        }).eq("id", task_id).execute()

    except Exception as e:
        supabase.table("tasks").update({
            "status": "failed",
            "error_message": _friendly_error(e)
        }).eq("id", task_id).execute()
        raise
