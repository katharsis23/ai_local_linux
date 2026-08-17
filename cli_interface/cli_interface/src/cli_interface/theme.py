# theme.py
from textual.theme import Theme

CYBER_NIGHT_THEME = Theme(
    name="cyber_night",
    primary="#6c5ce7",    # vivid-purple
    secondary="#0984e3",  # vivid-red
    accent="#a29bfe",     # light-purple
    background="#1e1e24",   # purple-gray
    surface="#2a2a35",    # Sidebar/input
    error="#ff7675",      # Coral
    success="#55efc4",    # Mint
    warning="#ffeaa7"
)

APP_CSS = """
Screen {
    background: $background;
}

#main_layout {
    height: 1fr;
}

ChatSidebar {
    width: 32;
    background: $surface;
    border-right: tall #6c5ce7;
    padding: 1;
}

ChatSidebar ListItem {
    padding: 1;
    margin: 0 1;
    border-radius: 4;
    background: transparent;
    color: #b2bec3;
}

ChatSidebar ListItem:hover {
    background: #0984e3 20%;
    color: $accent;
}

ChatSidebar ListItem.--focus {
    background: #6c5ce7 40%;
    color: #ffffff;
    text-style: bold;
}

ChatArea {
    width: 1fr;
    height: 1fr;
}

#chat_history {
    height: 1fr;
    overflow-y: scroll;
    padding: 1 2;
}

Input {
    dock: bottom;
    margin: 1;
    border: tall #6c5ce7;
    background: $surface;
    color: #ffffff;
}

Input:focus {
    border: tall #0984e3;
"""