from pathlib import Path
from typing import Optional, List
from fastapi import Depends
from logger import logger
from src.ai_local_daemon.config.settings import Settings
from src.ai_local_daemon.helper import normalize_path
from src.ai_local_daemon.internal.approval import ApprovalManager


class FileManager:
    def __init__(
        self,
        settings: Settings,
        approval_manager: ApprovalManager
    ):
        self.settings = settings
        self.approval_manager = approval_manager

    def _is_allowed(self, path: Path) -> bool:
        for allowed in self.settings.white_list_directories:
            if path.is_relative_to(normalize_path(allowed)):
                return True
        return False

    def _is_forbidden(self, path: Path) -> bool:
        for forbidden in self.settings.black_list_directories:
            if path.is_relative_to(Path(forbidden)):
                return True
        return False

    async def provide_file(self, path: str) -> Optional[bytes]:
        try:
            resolved = Path(path).expanduser().resolve()
            # does not exist
            if not resolved.exists():
                return None

            # forbidden ALWAYS wins
            if self._is_forbidden(resolved):
                return None

            # allowed
            if self._is_allowed(resolved):
                return self._read_file(resolved)

            if resolved.is_dir():
                # TODO: Implement explicit directory API
                # files =self._list_directory(resolved)
                # for file in files:
                #     return self._read_file(file)
                return None


            # requires approval
            approved = await self._request_file(resolved)
            if approved:
                return self._read_file(resolved)

            return None

        except Exception as error:
            logger.error("Failed to provide file", exc_info=True)
            raise error

    def _read_file(self, path: Path) -> bytes:

        if not path.is_file():
            raise ValueError("Not a file")
        size = path.stat().st_size

        if size > self.settings.max_file_size:
            raise ValueError("File too large")

        with open(path, "rb") as f:
            return f.read()

    async def _request_file(
        self,
        path: Path
    ) -> bool:
        """
        You will implement this later:
        - send request to frontend
        - wait for approval
        """

        approved = await self.approval_manager.make_request(
            type_="file",
            path=str(path),
        )

        return approved


class DirectoryManager:
    def __init__(
        self,
        settings: Settings,
        approval_manager: ApprovalManager
    ):
        self.settings = settings
        self.approval_manager = approval_manager

    def _is_allowed(self, path: Path) -> bool:
        for allowed in self.settings.white_list_directories:
            if path.is_relative_to(normalize_path(allowed)):
                return True
        return False

    def _is_forbidden(self, path: Path) -> bool:
        for forbidden in self.settings.black_list_directories:
            if path.is_relative_to(normalize_path(forbidden)):
                return True
        return False

    def _list_directory(self, path: Path) -> List[str]:
        try:
            if not path.is_dir():
                raise ValueError("Not a directory")

            files_list = list(path.iterdir())

            if len(files_list) > self.settings.max_files:
                raise ValueError("Directory too large")

            return [str(file) for file in files_list]

        except Exception:
            logger.error("Failed to list directory", exc_info=True)
            raise

    async def provide_directory(
        self,
        path: str
    ) -> Optional[List[str]]:
        try:
            resolved = Path(path).expanduser().resolve()

            # does not exist
            if not resolved.exists():
                return None

            # must be a directory
            if not resolved.is_dir():
                return None

            # forbidden ALWAYS wins
            if self._is_forbidden(resolved):
                return None

            # allowed
            if self._is_allowed(resolved):
                return self._list_directory(resolved)

            # requires approval
            approved = await self.request_access_to_directory(
                str(resolved)
            )

            if approved:
                return self._list_directory(resolved)

            return None

        except Exception:
            logger.error("Failed to provide directory", exc_info=True)
            raise

    async def request_access_to_directory(
        self,
        path: str
    ) -> bool:
        """
        Sends approval request to frontend/user
        """

        approved = await self.approval_manager.make_request(
            type_="directory",
            path=path,
        )

        return approved
