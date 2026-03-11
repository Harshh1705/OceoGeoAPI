## chatbot shi
from agno.agent import Agent
from agno.models.ollama import Ollama
# from config import MODEL

agent = Agent(
    model = Ollama(id="qwen3:0.6b"),
    markdown = True
)

agent.print_response("Share a 2 sentence horror story.")