"""Inspector screen for EvalEDS."""

from pathlib import Path

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class InspectorScreen(Screen):
    """Displays details for the currently selected item."""

    def set_text(self, message: str) -> None:
        """Replace the Inspector content with a text message."""

        content = self.ids.get("inspector_content")
        if content is None:
            return

        content.clear_widgets()
        content.add_widget(
            Label(
                text=message,
                size_hint_y=None,
                height=dp(42),
                halign="left",
                valign="middle",
                text_size=(content.width, None),
                color=(0.25, 0.28, 0.32, 1),
            )
        )

    def clear_content(self) -> None:
        """Remove all Inspector content."""

        content = self.ids.get("inspector_content")
        if content is not None:
            content.clear_widgets()


Builder.load_file(str(Path(__file__).with_suffix(".kv")))
