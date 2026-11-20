"""
Logging screen for EvalEDS.
"""

from pathlib import Path

from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.uix.screenmanager import Screen


class LoggingScreen(Screen):
    """Displays EDS connection information and application activity."""

    # Connection summary
    connection_state = StringProperty("Not tested")
    connection_state_color = ListProperty(
        [0.45, 0.45, 0.45, 1]
    )
    connection_endpoint = StringProperty("Not configured")
    last_attempt = StringProperty("Never")
    last_result = StringProperty("No connection attempt recorded.")

    # --------------------------------------------------------
    # Update connection summary
    # --------------------------------------------------------

    def update_connection_status(
        self,
        state: str,
        endpoint: str = "Not configured",
        last_attempt: str = "Never",
        message: str = "No connection attempt recorded."
    ) -> None:
        """Update the connection summary."""

        self.connection_state = state
        self.connection_endpoint = endpoint
        self.last_attempt = last_attempt
        self.last_result = message

        # Set state colour.
        if state == "Connected":
            self.connection_state_color = [0.1, 0.55, 0.2, 1]

        elif state == "Connecting":
            self.connection_state_color = [0.85, 0.55, 0.05, 1]

        elif state == "Disconnected":
            self.connection_state_color = [0.8, 0.15, 0.15, 1]

        else:
            self.connection_state_color = [0.45, 0.45, 0.45, 1]

    # --------------------------------------------------------
    # Activity log
    # --------------------------------------------------------

    def add_message(self, message: str, level: str = "INFO") -> None:
        """Append a message to the application log."""

        output = self.ids.status_output

        output.text += f"\n[{level}] {message}"
        output.cursor = (0, len(output.text))

    def clear_messages(self) -> None:
        """Clear the application log."""

        self.ids.status_output.text = ""


Builder.load_file(
    str(Path(__file__).with_suffix(".kv"))
)