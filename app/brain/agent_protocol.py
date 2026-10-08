"""Structured agent request/response contract.

The UI, voice worker, and future autonomous agent can use the same envelope.
The natural-language user input remains untouched inside input.text.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import uuid


PROTOCOL_VERSION = "1.0"


@dataclass
class AgentRequest:
    text: str
    source: str = "text"
    session_id: Optional[str] = None
    language: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self):
        data = asdict(self)
        data["protocol_version"] = PROTOCOL_VERSION
        data["session_id"] = self.session_id or str(uuid.uuid4())
        data["input"] = {"text": data.pop("text"), "language": data.pop("language")}
        return data


@dataclass
class AgentResponse:
    success: bool
    response: str
    action: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    error: Optional[str] = None

    def to_dict(self):
        return {
            "protocol_version": PROTOCOL_VERSION,
            "success": self.success,
            "response": self.response,
            "action": self.action,
            "needs_confirmation": self.needs_confirmation,
            "error": self.error,
        }
