from typing import Dict, Any, List, Optional
import json
import re

from httpx import AsyncClient
from logger import logger

from src.ai_local_daemon.internal.tool_calling import (
    FileManager,
    DirectoryManager,
)
from src.ai_local_daemon.wrappers.config import ConfigManager


class Agent:
    def __init__(
        self,
        config_manager: ConfigManager,
        file_manager: FileManager,
        directory_manager: DirectoryManager,
    ):
        self.config_manager = config_manager
        self.settings = self.config_manager.settings

        self.file_manager = file_manager
        self.directory_manager = directory_manager

        self.llama_url = "http://localhost:11434/api/chat"

    # -------------------------
    # PUBLIC ENTRY
    # -------------------------
    async def run(self, prompt: str) -> str:
        try:
            messages: List[dict] = [
                {
                    "role": "system",
                    "content": self.settings.default_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            model_response = await self._call_model(messages)

            if not model_response:
                return "Model failed to respond"

            tool_call = self._extract_tool_call(model_response)

            # No tool usage → direct answer
            if not tool_call:
                return model_response

            tool_result = await self._execute_tool(tool_call)

            # IMPORTANT: continue conversation correctly
            messages.append({
                "role": "assistant",
                "content": model_response,
            })

            # ⚠️ IMPORTANT FIX:
            # Ollama DOES NOT reliably support "tool" role
            messages.append({
                "role": "user",
                "content": f"[TOOL RESULT]\n{tool_result}",
            })

            final_response = await self._call_model(messages)

            if not final_response:
                return "Tool executed but model failed to respond"

            return final_response

        except Exception:
            logger.error("Failed to run agent", exc_info=True)
            return "Internal agent error"

    # -------------------------
    # MODEL CALL
    # -------------------------
    async def _call_model(self, messages: list[dict]) -> str:
        try:
            async with AsyncClient(timeout=3600) as client:
                response = await client.post(
                    url=self.llama_url,
                    json={
                        "model": self.settings.model_name,
                        "messages": messages,
                        "stream": False,
                    },
                )

            data = response.json()

            # 🔥 IMPORTANT: handle Ollama errors safely
            if "error" in data:
                logger.error(f"Ollama error: {data['error']}")
                return ""

            message = data.get("message", {})
            content = message.get("content")

            if not isinstance(content, str) or not content.strip():
                logger.error("Empty or invalid model response")
                return ""

            return content

        except Exception:
            logger.error("Failed to call model", exc_info=True)
            return ""

    # -------------------------
    # TOOL PARSING
    # -------------------------
    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        if not isinstance(text, str):
            return None

        match = re.search(r'\{.*"action".*\}', text, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except Exception:
            logger.error("Failed to parse tool call JSON", exc_info=True)
            return None

    # -------------------------
    # TOOL EXECUTION
    # -------------------------
    async def _execute_tool(self, tool_call: Dict[str, Any]) -> str:
        try:
            action_type = tool_call.get("action")
            args = tool_call.get("args", {})

            # ---------------- FILE ----------------
            if action_type == "read_file":
                path = args.get("path")
                if not path:
                    return "Missing path"

                content = await self.file_manager.provide_file(path)

                if not content:
                    return "Access rejected"

                try:
                    return content.decode("utf-8", errors="ignore")
                except Exception:
                    return "Binary file received"

            # ---------------- DIRECTORY ----------------
            if action_type == "read_directory":
                path = args.get("path")
                if not path:
                    return "Missing path"

                content = await self.directory_manager.provide_directory(path)

                if not content:
                    return "Access rejected"

                return str(content)

            return "Unknown tool"

        except Exception:
            logger.error("Failed to execute tool", exc_info=True)
            return "Tool execution failed"
