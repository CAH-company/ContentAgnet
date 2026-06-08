import os
from dotenv import load_dotenv
from db.supabase_client import supabase
from agents.crew import ContentMarketingCrew

load_dotenv()


def run_agent_task(task_id: str, revision: bool = False):
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

        crew = ContentMarketingCrew()
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
            "error_message": str(e)
        }).eq("id", task_id).execute()
        raise
