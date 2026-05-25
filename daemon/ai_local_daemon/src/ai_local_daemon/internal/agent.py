from typing import Dict, Any, List, Optional
import json
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

        # max tool iterations
        self.max_iter = 3

    # -------------------------------------------------
    # PUBLIC ENTRY
    # -------------------------------------------------
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

            iteration = 0

            while iteration < self.max_iter:

                model_response = await self._call_model(messages)

                if not model_response:
                    return "Model failed to respond"

                logger.info(f"MODEL RESPONSE:\n{model_response}")

                tool_call = self._extract_tool_call(model_response)

                # -------------------------------------------------
                # NO TOOL CALL -> FINAL ANSWER
                # -------------------------------------------------
                if not tool_call:
                    return model_response

                logger.info(f"TOOL CALL: {tool_call}")

                tool_result = await self._execute_tool(tool_call)
                tool_result = self._normalize_tool_result(tool_result)

                logger.info(f"TOOL RESULT:\n{tool_result}")

                # -------------------------------------------------
                # SAVE ASSISTANT TOOL REQUEST
                # -------------------------------------------------
                messages.append({
                    "role": "assistant",
                    "content": model_response,
                })

                # -------------------------------------------------
                # IMPORTANT:
                # tell model what happened
                # -------------------------------------------------
                messages.append({
                    "role": "user",
                    "content": "\n".join([
                        "[TOOL RESULT]",
                        tool_result,
                        "",
                        "If more information is required, request another tool.",
                        "Otherwise provide the final answer."
                    ])
                })

                iteration += 1

            # -------------------------------------------------
            # TOO MANY TOOL CALLS
            # -------------------------------------------------
            return "Stopped after maximum tool iterations"

        except Exception:
            logger.error("Failed to run agent", exc_info=True)
            return "Internal agent error"

    # -------------------------------------------------
    # MODEL CALL
    # -------------------------------------------------
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

            logger.info(f"HTTP status: {response.status_code}")

            data = response.json()

            logger.info(data)

            # Ollama error
            if "error" in data:
                logger.error(f"Ollama error: {data['error']}")
                return ""

            message = data.get("message")

            if not message:
                logger.error("No message in Ollama response")
                return ""

            content = message.get("content")

            if not isinstance(content, str):
                logger.error("Invalid content type")
                return ""

            if not content.strip():
                logger.error("Empty model response")
                return ""

            return content

        except Exception:
            logger.error("Failed to call model", exc_info=True)
            return ""

    # -------------------------------------------------
    # TOOL PARSING
    # -------------------------------------------------
    def _extract_tool_call(
        self,
        text: str
    ) -> Optional[Dict[str, Any]]:

        if not isinstance(text, str):
            return None

        start = text.find("{")

        if start == -1:
            return None

        brace_count = 0
        end = None

        for i in range(start, len(text)):
            char = text[i]

            if char == "{":
                brace_count += 1

            elif char == "}":
                brace_count -= 1

                if brace_count == 0:
                    end = i + 1
                    break

        if end is None:
            return None

        json_str = text[start:end]

        try:
            parsed = json.loads(json_str)

            if not isinstance(parsed, dict):
                return None

            if "action" not in parsed:
                return None

            return parsed

        except Exception:
            logger.error(
                "Failed to parse tool call JSON",
                exc_info=True
            )

            logger.error(f"RAW JSON:\n{json_str}")

            return None
    # -------------------------------------------------
    # TOOL EXECUTION
    # -------------------------------------------------
    async def _execute_tool(
        self,
        tool_call: Dict[str, Any]
    ) -> str:

        try:
            action_type = tool_call.get("action")
            args = tool_call.get("args", {})

            # -------------------------------------------------
            # READ FILE
            # -------------------------------------------------
            if action_type == "read_file":

                path = args.get("path")

                if not path:
                    return "Missing path"

                logger.info(f"READ FILE: {path}")

                content = await self.file_manager.provide_file(path)

                if not content:
                    return "Access rejected or file not found"

                try:
                    decoded = content.decode(
                        "utf-8",
                        errors="ignore"
                    )

                    return decoded

                except Exception:
                    return "Binary file received"

            # -------------------------------------------------
            # READ DIRECTORY
            # -------------------------------------------------
            elif action_type == "read_directory":

                path = args.get("path")

                if not path:
                    return "Missing path"

                logger.info(f"READ DIRECTORY: {path}")

                content = await self.directory_manager.provide_directory(path)

                if not content:
                    return "Access rejected or directory empty"

                return "\n".join([
                    str(item)
                    for item in content
                ])

            # -------------------------------------------------
            # UNKNOWN TOOL
            # -------------------------------------------------
            return f"Unknown tool: {action_type}"

        except Exception:
            logger.error(
                "Failed to execute tool",
                exc_info=True
            )

            return "Tool execution failed"
        

    def _normalize_tool_result(self, result: Any) -> str:

        if result is None:
            return "No result"

        if isinstance(result, str):
            return result

        if isinstance(result, bytes):
            return result.decode("utf-8", errors="ignore")

        if isinstance(result, list):
            return "\n".join(str(x) for x in result)

        if isinstance(result, dict):
            return json.dumps(result, indent=2)

        return str(result)