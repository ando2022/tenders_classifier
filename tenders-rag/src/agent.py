import json

from . import tools
from .core import llm


class Agent:
    def __init__(self):
        # Let's follow OpenAI's standard: `{"role", "content", "tool_calls"?}`
        self.history = [{"role": "system", "content": """You are a pirate scholar with access to Romeo and Juliet text via RAG and Wikipedia knowledge. 

SEARCH STRATEGY:
- For complex questions, break them down into specific searches
- Use multiple targeted RAG searches (e.g., "Tybalt sword fight death", "Friar Lawrence potion plan", "Romeo suicide Juliet tomb")
- Use specific Wikipedia searches for historical context (e.g., "Renaissance Italy", "Verona history", "Italian feuds 1500s")
- Combine information from both sources to give comprehensive answers

RAG SEARCH TIPS:
- Search for specific character names, plot events, scenes
- Use concrete nouns (poison, sword, balcony, tomb, marriage)
- Try different phrasings if first search doesn't work

Only answer based on information you actually find. If searches don't return relevant results, try different search terms or tell the user you couldn't find the information."""}]

        self.tools = [
            tools.rag.RagTool(),
            tools.wiki.WikiTool(),
        ]
        self.tools_by_name = {t.name: t for t in self.tools}
        
        # Preload RAG index so progress is shown at startup
        print("[*] Preloading RAG index...")
        tools.rag._get_index()

    def run_turn(self, user_text: str) -> str:
        # Add user message to our state
        self.history.append({"role": "user", "content": user_text})

        while True:  # Repeat this until....  ***
            response = llm.chat(
                self.history, self.tools
            )  # after first time, history contains tool outputs
            # either a message or a list of tool calls

            # Either LLM decided to call tools, or to answer
            if response.message:
                # Just an answer: save to history, and return the text
                self.history.append({"role": "assistant", "content": response.message})

                # *** the model decided to not call tools and send an answer back
                return response.message
                # We're done

            elif response.tool_calls:
                self.history.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": response.original_tool_calls,
                    }
                )

                for tool_call in response.tool_calls:
                    tool = self.tools_by_name.get(tool_call.name)
                    print(f"(calling {tool.name}...)")
                    output = tool.run(tool_call.args)
                    self.history.append(
                        {
                            "role": "tool",
                            "content": json.dumps(output),
                            "tool_call_id": tool_call.id,
                        }
                    )

            # I ran all the requested tools... now I need to call the model again to give it the results

        return None
