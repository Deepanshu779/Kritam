import re
import datetime
from typing import AsyncGenerator
import asyncio
from app.services.ai.base import BaseAIProvider
from app.services.automation.policy_engine import policy_engine
from app.schemas.action import ActionRequest

class OfflineRouter(BaseAIProvider):
    """
    Offline deterministic router for Kritam.
    Provides instant, zero-network conversational capabilities, local commands,
    math, time, system status, and desktop action execution.
    """

    async def is_available(self) -> bool:
        return True

    def extract_desktop_intent(self, prompt: str) -> dict | None:
        """Analyze if prompt is an action command (app launch, URL, folder, etc.)."""
        lower = prompt.lower().strip()
        
        # App launch pattern
        app_match = re.search(r"^(?:hey\s+kritam[,.]?\s*)?(?:please\s+)?(?:open|launch|start|run)\s+([a-zA-Z0-9\s._-]+)$", lower)
        if app_match:
            raw_target = app_match.group(1).strip()
            # Check if target is a known URL / domain
            if raw_target.endswith((".com", ".org", ".net", ".io", ".dev", ".ai", ".in")) or raw_target in ["youtube", "github", "google", "reddit", "stackoverflow"]:
                return {"type": "open_url", "target": raw_target}
            elif "folder" in raw_target or "directory" in raw_target:
                return {"type": "open_folder", "target": raw_target.replace("folder", "").replace("directory", "").strip()}
            else:
                return {"type": "launch_app", "target": raw_target}
        
        # URL pattern
        url_match = re.search(r"^(?:hey\s+kritam[,.]?\s*)?(?:go\s+to|navigate\s+to|visit)\s+([^\s]+)$", lower)
        if url_match:
            return {"type": "open_url", "target": url_match.group(1)}

        return None

    def is_deterministic_query(self, prompt: str) -> bool:
        """Check if query should be handled locally without cloud AI."""
        if self.extract_desktop_intent(prompt):
            return True
        lower = prompt.lower().strip()
        time_keywords = [
            "what time", "current time", "tell me the time", "what's the time",
            "what date", "today's date", "what is the date", "current date"
        ]
        if any(w in lower for w in time_keywords):
            return True
        if any(w in lower for w in ["who are you", "what are you", "what can you do", "introduce yourself"]):
            return True
        math_match = re.search(r"^(?:calculate|what is|compute)?\s*([0-9\s\+\-\*\/\^\(\)\.\%]+)$", lower)
        if math_match and len(math_match.group(1).strip()) > 1 and re.match(r"^[0-9\+\-\*\/\(\)\.\s]+$", math_match.group(1).strip()):
            return True
        return False

    async def generate_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "").strip()
                break

        lower = user_message.lower().strip()
        
        # 1. Action intents (e.g. "open vs code", "open chrome")
        intent = self.extract_desktop_intent(user_message)
        if intent:
            if intent["type"] == "launch_app":
                target_app = intent["target"]
                app_name = target_app.title()
                # Execute genuine desktop launch via policy engine
                action_res = policy_engine.execute_action(ActionRequest(action_type="launch_app", target=target_app))
                if action_res.success:
                    chunks = [
                        f"I have opened **{app_name}** for you.\n\n",
                        f"```action\n{{\"action_type\": \"launch_app\", \"target\": \"{target_app}\"}}\n```\n",
                        f"Status: {action_res.message}"
                    ]
                else:
                    chunks = [
                        f"Attempted to open **{app_name}**:\n\n",
                        f"{action_res.message}\n\n",
                        f"```action\n{{\"action_type\": \"launch_app\", \"target\": \"{target_app}\"}}\n```"
                    ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.03)
                return

            elif intent["type"] == "open_url":
                target = intent["target"]
                url = target if target.startswith("http") else f"https://www.{target}.com" if "." not in target else f"https://{target}"
                action_res = policy_engine.execute_action(ActionRequest(action_type="open_url", target=url))
                chunks = [
                    f"Opening **{url}** in your default browser.\n\n",
                    f"```action\n{{\"action_type\": \"open_url\", \"target\": \"{url}\"}}\n```\n",
                    action_res.message if action_res.success else f"Error: {action_res.message}"
                ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.03)
                return

            elif intent["type"] == "open_folder":
                folder = intent["target"]
                action_res = policy_engine.execute_action(ActionRequest(action_type="open_folder", target=folder))
                chunks = [
                    f"Opening your **{folder.title()}** folder.\n\n",
                    f"```action\n{{\"action_type\": \"open_folder\", \"target\": \"{folder}\"}}\n```\n",
                    action_res.message if action_res.success else f"Error: {action_res.message}"
                ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.03)
                return

        # 2. Date and Time queries
        time_keywords = ["what time", "current time", "tell me the time", "what's the time"]
        date_keywords = ["what date", "today's date", "what is the date", "current date"]
        is_time = any(w in lower for w in time_keywords)
        is_date = any(w in lower for w in date_keywords)

        if is_time and is_date:
            now = datetime.datetime.now()
            yield f"Today is **{now.strftime('%A, %B %d, %Y')}** and the current time is **{now.strftime('%I:%M %p')}**."
            return
        elif is_time:
            now = datetime.datetime.now()
            yield f"The current time is **{now.strftime('%I:%M %p')}**."
            return
        elif is_date:
            now = datetime.datetime.now()
            yield f"Today is **{now.strftime('%A, %B %d, %Y')}**."
            return

        # 3. Identity and role
        if any(w in lower for w in ["who are you", "what are you", "what can you do", "introduce yourself"]):
            response = (
                "I am **Kritam**, your personal desktop AI companion.\n\n"
                "I am designed to help you think, learn, research, code, organize tasks, and operate your computer through natural conversation.\n\n"
                "### What I can do:\n"
                "- **Conversations & Learning**: Answer questions, explain concepts, and brainstorm.\n"
                "- **Coding Assistance**: Guide project architecture, debug issues, and format code.\n"
                "- **Desktop Actions**: Launch approved applications (e.g., VS Code, Chrome, Calculator), open safe URLs, and navigate folders.\n"
                "- **Voice Interaction**: Talk to me via speech and interrupt me whenever you want.\n"
                "- **Hybrid AI**: Run locally via Ollama, connect to cloud AI models (OpenAI/Groq/OpenRouter), or work completely offline."
            )
            for part in response.split(" "):
                yield part + " "
                await asyncio.sleep(0.02)
            return

        # 4. Math / Calculation queries
        math_match = re.search(r"^(?:calculate|what is|compute)?\s*([0-9\s\+\-\*\/\^\(\)\.\%]+)$", lower)
        if math_match:
            expr = math_match.group(1).strip()
            if re.match(r"^[0-9\+\-\*\/\(\)\.\s]+$", expr) and len(expr) > 1:
                try:
                    result = eval(expr, {"__builtins__": None}, {})
                    yield f"**{expr}** = **{result}**"
                    return
                except Exception:
                    pass

        # 5. Default conversational fallback
        response = (
            f"I received your message: \"{user_message}\".\n\n"
            "Kritam is currently running in **Offline Mode**.\n\n"
            "To unlock open-ended reasoning, deep research, and advanced coding intelligence:\n"
            "1. Open **Settings** (gear icon in the sidebar).\n"
            "2. Select **Cloud AI** and enter an API key (OpenAI, Groq, or OpenRouter), or\n"
            "3. Select **Local AI (Ollama)** to run models like Qwen or Llama locally on your PC without cloud dependency.\n\n"
            "In the meantime, you can ask me to open desktop applications, check the date/time, perform calculations, or manage your local conversations."
        )
        for part in response.split(" "):
            yield part + " "
            await asyncio.sleep(0.02)
