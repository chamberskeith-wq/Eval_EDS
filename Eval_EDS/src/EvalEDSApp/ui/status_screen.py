"""
Created on Nov 17, 2026

@author: keith.chambers


Status screen for EvalEDS.
"""

from kivy.uix.screenmanager import Screen


class StatusScreen(Screen):
    """Displays application activity and status messages."""

    def add_message(self, message: str, level: str = "INFO") -> None:
        """Append a message to the status output."""

        output = self.ids.status_output

        output.text += f"\n[{level}] {message}"
        output.cursor = (0, len(output.text))

    def clear_messages(self) -> None:
        """Clear the status output."""

        self.ids.status_output.text = ""


from pathlib import Path
from kivy.lang import Builder

Builder.load_file(
    str(Path(__file__).with_suffix(".kv"))
)