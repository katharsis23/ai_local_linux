import asyncio
import os
import subprocess
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual import on, work
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label, Markdown, Button

# API Library
from src.cli_interface.api.client import ApiClient
from src.cli_interface.api.chat import ChatClient
from src.cli_interface.api.prompt import PromptClient
from src.cli_interface.api.approve import ApproveAPI


# Wrap constants and especially APIs into providers or figure better delivery
class CLIApp(App):
    """Main TUI client for Ollama"""
    SOCKET_PATH = f"/run/user/{os.getuid()}/ai_local_daemon/app.sock"
    CONFIG_PATH = os.path.expanduser("~/.config/ai_local_daemon/settings.json")

    def on_mount(self):
        base = ApiClient(self.SOCKET_PATH)
        self.chat_api = ChatClient(base)
        self.prompt_api = PromptClient(base)
        self.approve_api = ApproveAPI(base)

        self.current_request_id = None
        self.chat_content = "Awaiting your prompt. You can use special commands like `\\chat` / `\\config`"

    CSS = """
    #main_layout {
        height: 1fr;
    }
    #sidebar {
        width: 30;
        background: $surface;
        border-right: vkey $background;
    }
    #chat_container {
        width: 1fr;
        height: 1fr;
    }
    #chat_history {
        height: 1fr;
        overflow-y: scroll;
        padding: 1;
    }
    Input {
        dock: bottom;
        margin: 1 0 0 0;
    }
    #approval_bar {
        height: 3;
        margin: 1;
        align: right middle;
    }
    .hidden {
        display: none;
    }
    #approval_info {
        content-align: center middle;
        margin-right: 2;
    }
    Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Вихід"),
        ("ctrl+b", "toggle_sidebar", "Сайдбар"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main_layout"):
            yield ListView(
                #   TODO: Add dynamically
                id="sidebar",
            )

            with Vertical(id="chat_container"):
                yield Markdown(
                    "Awaiting your prompt. You can use special commands like `\\chat` / `\\config`",
                    id="chat_history"
                )
                with Horizontal(id="approval_bar", classes="hidden"):
                    yield Label("Pending request: ", id="approval_info")
                    yield Button("Approve", id="btn_approve", variant="success")
                    yield Button("Reject", id="btn_reject", variant="error")
                yield Input(placeholder="Enter your prompt...")
        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return

        event.input.value = ""

        if text.startswith("\\"):
            await self.handle_slash_command(text)
        else:
            self.send_prompt_to_socket(text)

    async def handle_slash_command(self, command_str: str) -> None:
        """Парсер спеціальних команд."""
        parts = command_str.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "\\chat":
            if args and args[0] == "new":
                sidebar = self.query_one("#sidebar", ListView)
                new_chat_idx = len(sidebar.children) + 1
                await sidebar.append(ListItem(Label(f"New chat {new_chat_idx}")))
                self.notify("New chat created")
            else:
                self.query_one("#sidebar").focus()

        elif cmd == "\\config":
            if args and args[0] == "path":
                self.notify(f"Config path: {self.CONFIG_PATH}")
            else:
                await self.open_editor()
        else:
            self.notify(f"Unknown command: {cmd}", severity="error")

    async def open_editor(self) -> None:
        # TODO: Add in config option default_editor
        editor = os.environ.get("EDITOR", "nano")

        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        if not os.path.exists(self.CONFIG_PATH):
            # Hanle error
            ...
        self.notify("Open editor...")
        with self.suspend():
            subprocess.run([editor, self.CONFIG_PATH])

    @work
    async def send_prompt_to_socket(self, prompt: str) -> None:
        chat_window = self.query_one("#chat_history", Markdown)

        self.chat_content += f"\n\n--- \n**You:** {prompt}\n\n**Agent:** "
        chat_window.update(self.chat_content)

        polling_worker = self.poll_approvals()

        try:
            # Use the properly configured API client instead of raw sockets
            response = await self.prompt_api.send_prompt(prompt)
            self.chat_content += response
            chat_window.update(self.chat_content)
        except Exception as e:
            chat_window.update(self.chat_content + f"\nError: {e}")
        finally:
            polling_worker.cancel()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    @work(exclusive=True)
    async def poll_approvals(self):
        while True:
            try:
                request = await self.approve_api.pending_requests()

                if request:
                    self.current_request_id = request.id_

                    info_text = (
                        f"Pending {request.type_}: "
                        f"{request.command or request.path}"
                    )

                    self.query_one("#approval_info", Label).update(info_text)
                    self.query_one("#approval_bar").remove_class("hidden")

            except Exception:
                pass

            await asyncio.sleep(2)


if __name__ == "__main__":
    app = CLIApp()
    app.run()
