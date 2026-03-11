import os
import logging

from services.NeondbService import NeonDBService
from core.chatbot import classify_intent, run_sql_agent, run_domain_agent

logger = logging.getLogger(__name__)

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "core", "prompts")


def _load_prompt(filename: str) -> str:
    path = os.path.join(_PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class ChatServiceOllama:
    """Orchestrates multi-agent chat: intent classification → SQL / Domain / Off-topic."""

    def __init__(self):
        self.db = NeonDBService()
        self.intent_prompt = _load_prompt("intent_prompt.md")
        self.sql_prompt = _load_prompt("sql_prompt.md")
        self.domain_prompt = _load_prompt("domain_prompt.md")

    def process_message(self, message: str, user_id: str, project_id: int) -> dict:
        """
        Classify the message intent and route to the appropriate agent.

        Returns a dict with at least {"intent": str, ...} plus intent-specific keys.
        """
        try:
            intent = classify_intent(message, self.intent_prompt)
        except Exception:
            logger.exception("Intent classification failed")
            intent = "OFF_TOPIC"

        if intent == "SQL":
            try:
                result = run_sql_agent(
                    message=message,
                    user_id=user_id,
                    project_id=project_id,
                    system_message=self.sql_prompt,
                    db=self.db,
                )
                return {"intent": "SQL", **result}
            except Exception:
                logger.exception("SQL agent failed")
                return {
                    "intent": "SQL",
                    "query": "",
                    "data": [],
                    "summary": "Sorry, I encountered an error while processing your data query. Please try again.",
                }

        if intent == "DOMAIN":
            try:
                response = run_domain_agent(message, self.domain_prompt)
                return {"intent": "DOMAIN", "response": response}
            except Exception:
                logger.exception("Domain agent failed")
                return {
                    "intent": "DOMAIN",
                    "response": "Sorry, I encountered an error. Please try again.",
                }

        # OFF_TOPIC
        return {
            "intent": "OFF_TOPIC",
            "response": (
                "I'm specialized in oceanographic and geospatial topics. "
                "I can't help with that, but feel free to ask me anything "
                "about ocean science or your Argo float data!"
            ),
        }
