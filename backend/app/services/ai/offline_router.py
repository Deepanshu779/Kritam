import re
import uuid
import json
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
    math, time, system status, music, search, and desktop action execution.
    """

    async def is_available(self) -> bool:
        return True

    def clean_command_text(self, prompt: str) -> str:
        """Strip conversational prefixes (e.g. 'Hey Kritam, can you please...') and suffixes."""
        text = prompt.strip()
        # Remove wake-word prefixes
        text = re.sub(r"^(?:(?:hey|hi|hello|ok|okay)\s+)?kritam[,.]?\s*", "", text, flags=re.IGNORECASE)
        # Remove polite request prefixes
        text = re.sub(r"^(?:please\s+|can\s+you\s+(?:please\s+)?|could\s+you\s+(?:please\s+)?|would\s+you\s+(?:please\s+)?|help\s+me\s+to\s+)", "", text, flags=re.IGNORECASE)
        # Remove polite suffixes
        text = re.sub(r"(?:\s+for\s+me|\s+please|\s+now)[.!?]*$", "", text, flags=re.IGNORECASE)
        return text.strip()

    def extract_desktop_intent(self, prompt: str) -> dict | None:
        """Analyze if prompt is an action command (app launch, URL, music, search, folder, etc.)."""
        cleaned = self.clean_command_text(prompt)
        lower = cleaned.lower()

        # 1. Cancellation / Stop speech
        if re.search(r"^(?:stop(?:\s+speaking|\s+talking)?|cancel(?:\s+that)?|be\s+quiet|shut\s+up|pause)$", lower):
            return {"type": "cancel_speech", "target": "stop"}

        # 2. Music & media playback (e.g., "play some lo-fi music", "play Bohemian Rhapsody on YouTube", "play songs on Spotify")
        play_match = re.search(r"^(?:play|listen\s+to)\s+(?:some\s+)?(.+)$", lower)
        if play_match:
            raw_target = play_match.group(1).strip()
            if raw_target in ["music", "a song", "some music", "songs", "tracks"]:
                raw_target = "lo-fi chill beats"
            return {"type": "play_music", "target": raw_target}

        # 3. Web Search (e.g., "search for C++ DSA tutorials", "google Python decorators")
        search_match = re.search(r"^(?:search(?:\s+for|\s+on\s+google)?|google)\s+(.+)$", lower)
        if search_match:
            query = search_match.group(1).strip()
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            return {"type": "open_url", "target": url, "label": f"Google search for '{query}'"}

        # 4. App launch pattern (e.g., "open Chrome", "launch vs code", "start calculator")
        app_match = re.search(r"^(?:open|launch|start|run)\s+(?:the\s+)?([a-zA-Z0-9\s._-]+)$", lower)
        if app_match:
            raw_target = app_match.group(1).strip()
            # Check if target is a known URL / domain
            if raw_target.endswith((".com", ".org", ".net", ".io", ".dev", ".ai", ".in")) or raw_target in [
                "youtube", "github", "google", "reddit", "stackoverflow", "gmail", "chatgpt", "twitter", "x.com", "linkedin", "wikipedia"
            ]:
                return {"type": "open_url", "target": raw_target}
            elif "folder" in raw_target or "directory" in raw_target:
                return {"type": "open_folder", "target": raw_target.replace("folder", "").replace("directory", "").strip()}
            elif raw_target in ["music", "spotify"]:
                return {"type": "play_music", "target": "spotify" if raw_target == "spotify" else "lo-fi music"}
            else:
                return {"type": "launch_app", "target": raw_target}

        # 5. URL navigation pattern (e.g., "go to github.com", "visit reddit.com")
        url_match = re.search(r"^(?:go\s+to|navigate\s+to|visit)\s+([^\s]+)$", lower)
        if url_match:
            return {"type": "open_url", "target": url_match.group(1)}

        # 6. Folder navigation pattern (e.g., "open my downloads folder", "show desktop directory")
        folder_match = re.search(r"^(?:open|show|explore)\s+(?:my\s+)?(downloads|documents|desktop|pictures|music|videos|home)\s*(?:folder|directory)?$", lower)
        if folder_match:
            return {"type": "open_folder", "target": folder_match.group(1)}

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
        
        # 1. Action intents (e.g. "open vs code", "play music", "open chrome")
        intent = self.extract_desktop_intent(user_message)
        if intent:
            if intent["type"] == "cancel_speech":
                chunks = ["I've stopped speaking. Let me know if you need anything else!"]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.02)
                return

            if intent["type"] == "play_music":
                target = intent["target"]
                action_res = policy_engine.execute_action(ActionRequest(action_type="play_music", target=target))
                action_payload = {
                    "action_id": str(uuid.uuid4()),
                    "action_type": "play_music",
                    "target": target,
                    "status": "succeeded" if action_res.success else "failed",
                    "executed": True,
                    "message": action_res.message
                }
                chunks = [
                    f"{action_res.message}\n\n",
                    f"```action\n{json.dumps(action_payload)}\n```\n",
                    f"Status: {action_res.message}"
                ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.02)
                return

            elif intent["type"] == "launch_app":
                target_app = intent["target"]
                app_name = target_app.title()
                # Execute genuine desktop launch via policy engine
                action_res = policy_engine.execute_action(ActionRequest(action_type="launch_app", target=target_app))
                action_payload = {
                    "action_id": str(uuid.uuid4()),
                    "action_type": "launch_app",
                    "target": target_app,
                    "status": "succeeded" if action_res.success else "failed",
                    "executed": True,
                    "message": action_res.message
                }
                if action_res.success:
                    chunks = [
                        f"I have opened **{app_name}** for you.\n\n",
                        f"```action\n{json.dumps(action_payload)}\n```\n",
                        f"Status: {action_res.message}"
                    ]
                else:
                    chunks = [
                        f"Attempted to open **{app_name}**:\n\n{action_res.message}\n\n",
                        f"```action\n{json.dumps(action_payload)}\n```\n",
                        f"Status: {action_res.message}"
                    ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.02)
                return

            elif intent["type"] == "open_url":
                target = intent["target"]
                url = target if target.startswith("http") else f"https://www.{target}.com" if "." not in target else f"https://{target}"
                action_res = policy_engine.execute_action(ActionRequest(action_type="open_url", target=url))
                action_payload = {
                    "action_id": str(uuid.uuid4()),
                    "action_type": "open_url",
                    "target": url,
                    "status": "succeeded" if action_res.success else "failed",
                    "executed": True,
                    "message": action_res.message
                }
                label = intent.get("label", f"Opening **{url}** in your default browser.")
                chunks = [
                    f"{label}\n\n",
                    f"```action\n{json.dumps(action_payload)}\n```\n",
                    action_res.message if action_res.success else f"Error: {action_res.message}"
                ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.02)
                return

            elif intent["type"] == "open_folder":
                folder = intent["target"]
                action_res = policy_engine.execute_action(ActionRequest(action_type="open_folder", target=folder))
                action_payload = {
                    "action_id": str(uuid.uuid4()),
                    "action_type": "open_folder",
                    "target": folder,
                    "status": "succeeded" if action_res.success else "failed",
                    "executed": True,
                    "message": action_res.message
                }
                chunks = [
                    f"Opening your **{folder.title()}** folder.\n\n",
                    f"```action\n{json.dumps(action_payload)}\n```\n",
                    action_res.message if action_res.success else f"Error: {action_res.message}"
                ]
                for c in chunks:
                    yield c
                    await asyncio.sleep(0.02)
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
