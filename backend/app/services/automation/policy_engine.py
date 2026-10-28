import os
import uuid
import webbrowser
from urllib.parse import urlparse
from pathlib import Path
from app.schemas.action import ActionRequest, ActionResponse, ActionPlan, RiskLevel
from app.services.automation.app_launcher import AppLauncher

ALLOWED_STANDARD_FOLDERS = {
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
    "home": Path.home()
}

class PolicyEngine:
    """Security and action execution policy engine."""

    @staticmethod
    def evaluate_risk(action_type: str, target: str) -> tuple[RiskLevel, bool, str]:
        """Determine risk tier and whether affirmative user confirmation is required."""
        if action_type in ["launch_app", "open_url", "open_folder", "inspect_file", "play_music"]:
            return RiskLevel.LOW, False, f"Read-only or approved application action: {action_type}"
        
        if action_type in ["create_file", "modify_file", "schedule_reminder"]:
            return RiskLevel.MEDIUM, True, f"Modifies local state or schedule: {action_type}"

        if action_type in ["delete_file", "run_script", "execute_system_command"]:
            return RiskLevel.HIGH, True, f"Potentially destructive or system modifying action: {action_type}"

        return RiskLevel.HIGH, True, f"Unknown action requires full confirmation: {action_type}"

    @classmethod
    def execute_action(cls, request: ActionRequest) -> ActionResponse:
        risk_level, requires_confirmation, desc = cls.evaluate_risk(request.action_type, request.target)

        # High or Medium risk requires confirmation before running
        if requires_confirmation and not request.confirmed:
            plan = ActionPlan(
                action_id=str(uuid.uuid4()),
                action_type=request.action_type,
                target=request.target,
                description=desc,
                risk_level=risk_level,
                requires_confirmation=True,
                consequences=f"Executing '{request.action_type}' targeting '{request.target}' will modify local files or settings."
            )
            return ActionResponse(
                success=False,
                action_type=request.action_type,
                target=request.target,
                message=f"Action requires explicit user confirmation ({risk_level.value.upper()} RISK).",
                requires_confirmation=True,
                plan=plan
            )

        # 1. Launch Application
        if request.action_type == "launch_app":
            ok, msg = AppLauncher.launch(request.target)
            return ActionResponse(success=ok, action_type=request.action_type, target=request.target, message=msg)

        # 2. Open URL
        elif request.action_type == "open_url":
            raw_url = request.target.strip()
            
            # Check for dangerous or forbidden schemes
            if ":" in raw_url:
                prefix = raw_url.split(":", 1)[0].lower()
                if prefix not in ["http", "https"]:
                    return ActionResponse(
                        success=False,
                        action_type=request.action_type,
                        target=request.target,
                        message=f"Invalid or untrusted URL scheme '{prefix}'. Only http/https URLs are permitted."
                    )
            
            if not raw_url.startswith(("http://", "https://")):
                raw_url = "https://" + raw_url
            
            parsed = urlparse(raw_url)
            if parsed.scheme not in ["http", "https"] or not parsed.netloc:
                return ActionResponse(
                    success=False,
                    action_type=request.action_type,
                    target=request.target,
                    message="Invalid or untrusted URL. Only http/https URLs are permitted."
                )

            try:
                webbrowser.open(raw_url)
                return ActionResponse(
                    success=True,
                    action_type=request.action_type,
                    target=raw_url,
                    message=f"Opened {raw_url} in your default browser."
                )
            except Exception as e:
                return ActionResponse(success=False, action_type=request.action_type, target=raw_url, message=str(e))

        # 3. Open Folder
        elif request.action_type == "open_folder":
            folder_key = request.target.lower().strip()
            target_path = ALLOWED_STANDARD_FOLDERS.get(folder_key)
            if not target_path:
                candidate = Path(request.target).expanduser().resolve()
                # Enforce path stays within user home directory
                if Path.home() in candidate.parents or candidate == Path.home():
                    target_path = candidate
                else:
                    return ActionResponse(
                        success=False,
                        action_type=request.action_type,
                        target=request.target,
                        message="Cannot open folder outside of your user directory without explicit approval."
                    )

            if not target_path.exists():
                return ActionResponse(
                    success=False,
                    action_type=request.action_type,
                    target=str(target_path),
                    message=f"Directory '{target_path}' does not exist."
                )

            try:
                os.startfile(str(target_path))
                return ActionResponse(
                    success=True,
                    action_type=request.action_type,
                    target=str(target_path),
                    message=f"Opened directory {target_path}."
                )
            except Exception as e:
                return ActionResponse(success=False, action_type=request.action_type, target=str(target_path), message=str(e))

        # 4. Safe file preview/inspect
        elif request.action_type == "inspect_file":
            file_path = Path(request.target).expanduser().resolve()
            if not file_path.exists() or not file_path.is_file():
                return ActionResponse(
                    success=False,
                    action_type=request.action_type,
                    target=request.target,
                    message=f"File not found: '{file_path}'"
                )
            # Size limit: 2MB for safe inspection
            if file_path.stat().st_size > 2 * 1024 * 1024:
                return ActionResponse(
                    success=False,
                    action_type=request.action_type,
                    target=request.target,
                    message="File is larger than 2MB limit for safe reading."
                )
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                # Truncate if very long
                preview = content[:2000] + ("\n... [Truncated]" if len(content) > 2000 else "")
                return ActionResponse(
                    success=True,
                    action_type=request.action_type,
                    target=str(file_path),
                    message=f"Read {file_path.name} successfully.",
                    output=preview
                )
            except Exception as e:
                return ActionResponse(success=False, action_type=request.action_type, target=str(file_path), message=str(e))

        # 5. Play Music (Spotify app or YouTube Music / Spotify Web)
        elif request.action_type == "play_music":
            import re
            import urllib.parse
            raw_target = request.target.strip()
            clean_query = re.sub(r"^(?:play|listen\s+to|some)\s+", "", raw_target, flags=re.IGNORECASE).strip()
            if not clean_query:
                clean_query = "lo-fi music"

            lower_query = clean_query.lower()
            if "spotify" in lower_query:
                ok, msg = AppLauncher.launch("spotify")
                if ok:
                    return ActionResponse(
                        success=True,
                        action_type=request.action_type,
                        target=clean_query,
                        message=f"Launched Spotify desktop application."
                    )
                # Fallback to web search
                search_term = re.sub(r"(?:\s+on\s+spotify|spotify)", "", clean_query, flags=re.IGNORECASE).strip() or "music"
                url = f"https://open.spotify.com/search/{urllib.parse.quote_plus(search_term)}"
                webbrowser.open(url)
                return ActionResponse(
                    success=True,
                    action_type=request.action_type,
                    target=url,
                    message=f"Opened Spotify Web for '{search_term}'."
                )
            else:
                search_term = re.sub(r"(?:\s+on\s+youtube|youtube)", "", clean_query, flags=re.IGNORECASE).strip() or "lo-fi music"
                url = f"https://music.youtube.com/search?q={urllib.parse.quote_plus(search_term)}"
                try:
                    webbrowser.open(url)
                    return ActionResponse(
                        success=True,
                        action_type=request.action_type,
                        target=url,
                        message=f"Playing '{search_term}' on YouTube Music."
                    )
                except Exception as e:
                    return ActionResponse(success=False, action_type=request.action_type, target=url, message=str(e))

        return ActionResponse(
            success=False,
            action_type=request.action_type,
            target=request.target,
            message=f"Unsupported action type: {request.action_type}"
        )

policy_engine = PolicyEngine()
