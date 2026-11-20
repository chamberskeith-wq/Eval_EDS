
"""EDS Administration screen for EvalEDS."""

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from EvalEDSApp.config import APP_NAMESPACE


logger = logging.getLogger(APP_NAMESPACE)


class EDSAdministrationScreen(Screen):
    """Retrieves and browses the EDS system configuration."""

    refreshing = BooleanProperty(False)
    retrieval_status = StringProperty("Configuration not retrieved")
    retrieval_time = StringProperty("Never")

    # Retain the complete EDS response.
    configuration_data = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Paths of expanded tree nodes.
        self._expanded_paths = set()

    # --------------------------------------------------------
    # Retrieve configuration
    # --------------------------------------------------------

    def on_refresh_configuration(self) -> None:
        """Start retrieving the EDS configuration."""

        if self.refreshing:
            return

        app = App.get_running_app()

        if app is None or not hasattr(app, "eds_connection_service"):
            self.retrieval_status = "EDS connection service unavailable"
            self._report_status(self.retrieval_status, "ERROR")
            return

        if app.eds_connection_service.active_profile is None:
            self.retrieval_status = "No EDS connection profile available"
            self._report_status(self.retrieval_status, "ERROR")
            return

        self.refreshing = True
        self.retrieval_status = "Retrieving EDS configuration..."

        self.clear_tree()
        self.clear_details()

        self._report_status("Retrieving EDS configuration...")

        self._retrieval_thread = Thread(
            target=self._configuration_worker,
            args=(app,),
            daemon=True,
            name="EDS-Configuration"
        )

        self._retrieval_thread.start()

    # --------------------------------------------------------
    # Background worker
    # --------------------------------------------------------

    def _configuration_worker(self, app) -> None:
        """Retrieve configuration outside the Kivy UI thread."""

        try:
            result = app.eds_connection_service.get_configuration()

        except Exception as exc:
            logger.exception(
                "Unexpected error retrieving EDS configuration"
            )

            message = str(exc)

            Clock.schedule_once(
                lambda dt, msg=message:
                    self._complete_retrieval(False, msg, None),
                0
            )
            return

        Clock.schedule_once(
            lambda dt, success=result.success,
                   msg=result.message, data=result.response_data:
                self._complete_retrieval(success, msg, data),
            0
        )

    # --------------------------------------------------------
    # Complete retrieval
    # --------------------------------------------------------

    def _complete_retrieval(
        self,
        success: bool,
        message: str,
        response_data: dict | list | None
    ) -> None:
        """Process the result on Kivy's main thread."""

        self.refreshing = False

        if not success:
            self.retrieval_status = "Configuration retrieval failed"
            self.configuration_data = None
            self.clear_tree()
            self.clear_details(message)

            logger.warning(
                "EDS configuration retrieval failed: %s",
                message
            )

            self._report_status(
                f"EDS configuration retrieval failed: {message}",
                "ERROR"
            )
            return

        if not isinstance(response_data, dict):
            self.retrieval_status = "Invalid configuration response"
            self.configuration_data = response_data
            self.clear_tree()
            self.clear_details(
                "The EDS response did not contain a JSON object."
            )
            self._report_status(
                "EDS returned an invalid configuration structure.",
                "ERROR"
            )
            return

        self.configuration_data = response_data

        self.retrieval_time = (
            datetime.now().astimezone().strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
        )

        self.retrieval_status = "Configuration retrieved successfully"

        self.build_configuration_tree()

        self._report_status(
            "EDS configuration retrieved successfully."
        )

    # --------------------------------------------------------
    # Build configuration tree
    # --------------------------------------------------------

    def build_configuration_tree(self) -> None:
        """Build the initial tree from the complete JSON response."""

        self.clear_tree()
        self.clear_details()

        if not isinstance(self.configuration_data, dict):
            self.clear_details("No valid configuration data is available.")
            return

        # Expand the main sections initially.
        self._expanded_paths = {
            (key,)
            for key in self.configuration_data
            if isinstance(self.configuration_data[key], (dict, list))
            and self.configuration_data[key]
        }

        # Also expand the Components array under System.
        components_path = ("System", "Components")
        components = self._get_value(components_path)

        if isinstance(components, list) and components:
            self._expanded_paths.add(components_path)

        self._render_tree()

        self.ids.selected_component_title.text = "EDS Configuration"
        self.ids.selected_component_type.text = "Select an item to inspect its value."
        self.ids.component_details.text = (
            "Configuration retrieved successfully.\n\n"
            "Select a section, component or property from the tree."
        )

    def _render_tree(self) -> None:
        """Render all currently visible tree nodes."""

        self.ids.component_list.clear_widgets()

        if not isinstance(self.configuration_data, dict):
            return

        for key, value in self.configuration_data.items():
            self._add_tree_node(
                label=str(key),
                value=value,
                path=(key,),
                depth=0
            )

    def _add_tree_node(
        self,
        label: str,
        value,
        path: tuple,
        depth: int
    ) -> None:
        """Add a tree node and recursively add expanded children."""

        is_container = isinstance(value, (dict, list))
        has_children = is_container and bool(value)

        expanded = path in self._expanded_paths

        if has_children:
            prefix = "[-] " if expanded else "[+] "
        else:
            prefix = "    "

        indentation = "    " * depth

        if isinstance(value, dict):
            display_label = f"{prefix}{label} ({len(value)})"
        elif isinstance(value, list):
            display_label = f"{prefix}{label} [{len(value)}]"
        else:
            display_label = f"{prefix}{label}: {self._format_value(value)}"

        button = Button(
            text=indentation + display_label,
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            padding=(dp(6), 0),
            background_normal="",
            background_color=(0.88, 0.90, 0.93, 1),
            color=(0.18, 0.22, 0.28, 1),
            font_size="13sp"
        )

        button.bind(
            on_release=lambda instance, node_path=path:
                self.on_tree_node_selected(node_path)
        )

        self.ids.component_list.add_widget(button)

        if not expanded:
            return

        if isinstance(value, dict):
            for child_key, child_value in value.items():
                self._add_tree_node(
                    label=str(child_key),
                    value=child_value,
                    path=path + (child_key,),
                    depth=depth + 1
                )

        elif isinstance(value, list):
            for index, child_value in enumerate(value):

                # Component entries are references to top-level
                # component configuration objects.
                if (
                    path == ("System", "Components")
                    and isinstance(child_value, dict)
                ):
                    component_id = child_value.get(
                        "componentId",
                        f"Component {index}"
                    )
                    component_type = child_value.get(
                        "componentType",
                        "Unknown type"
                    )
                    child_label = (
                        f"{component_id} ({component_type})"
                    )
                else:
                    child_label = f"[{index}]"

                self._add_tree_node(
                    label=child_label,
                    value=child_value,
                    path=path + (index,),
                    depth=depth + 1
                )

    # --------------------------------------------------------
    # Tree selection
    # --------------------------------------------------------

    def on_tree_node_selected(self, path: tuple) -> None:
        """Expand, collapse or display the selected tree node."""

        value = self._get_value(path)

        if value is None and not self._path_exists(path):
            return

        # Component entries under System.Components refer to
        # their full configuration at the top level.
        if (
            len(path) == 3
            and path[:2] == ("System", "Components")
            and isinstance(value, dict)
        ):
            component_id = value.get("componentId")

            if component_id in self.configuration_data:
                component_path = (component_id,)
                self.display_configuration_item(
                    component_path,
                    self.configuration_data[component_id],
                    component_id
                )
                return

        # Expand or collapse non-empty dictionaries and lists.
        if isinstance(value, (dict, list)) and value:

            if path in self._expanded_paths:
                self._expanded_paths.remove(path)
            else:
                self._expanded_paths.add(path)

            self._render_tree()

        self.display_configuration_item(
            path,
            value,
            str(path[-1]) if path else "EDS Configuration"
        )

    def display_configuration_item(
        self,
        path: tuple,
        value,
        title: str
    ) -> None:
        """Display the selected item's value and data type."""

        if isinstance(value, dict):
            value_type = f"Object — {len(value)} properties"
        elif isinstance(value, list):
            value_type = f"Array — {len(value)} items"
        elif value is None:
            value_type = "Null"
        else:
            value_type = type(value).__name__

        self.ids.selected_component_title.text = title
        self.ids.selected_component_type.text = (
            f"{'.'.join(str(part) for part in path)} | {value_type}"
        )

        self.ids.component_details.text = json.dumps(
            value,
            indent=4,
            ensure_ascii=False,
            default=str
        )

        logger.info(
            "EDS Administration selected configuration item: %s",
            ".".join(str(part) for part in path)
        )

    # --------------------------------------------------------
    # Data helpers
    # --------------------------------------------------------

    def _get_value(self, path: tuple):
        """Return the value at a path in the configuration."""

        value = self.configuration_data

        try:
            for part in path:
                value = value[part]
            return value

        except (KeyError, IndexError, TypeError):
            return None

    def _path_exists(self, path: tuple) -> bool:
        """Check whether a configuration path exists."""

        value = self.configuration_data

        try:
            for part in path:
                value = value[part]
            return True

        except (KeyError, IndexError, TypeError):
            return False

    @staticmethod
    def _format_value(value) -> str:
        """Format scalar values for display in the tree."""

        if value is None:
            return "null"

        if isinstance(value, bool):
            return str(value)

        text = str(value)

        if len(text) > 35:
            return text[:32] + "..."

        return text

    # --------------------------------------------------------
    # Inspector helpers
    # --------------------------------------------------------

    def clear_tree(self) -> None:
        """Remove all tree nodes."""

        if "component_list" in self.ids:
            self.ids.component_list.clear_widgets()

        self._expanded_paths.clear()

        if "component_count" in self.ids:
            self.ids.component_count.text = "EDS Configuration"

    def clear_details(self, message: str = "") -> None:
        """Clear the selected configuration details."""

        if "selected_component_title" in self.ids:
            self.ids.selected_component_title.text = (
                "No item selected"
            )

        if "selected_component_type" in self.ids:
            self.ids.selected_component_type.text = ""

        if "component_details" in self.ids:
            self.ids.component_details.text = message

    # --------------------------------------------------------
    # Status reporting
    # --------------------------------------------------------

    @staticmethod
    def _report_status(
        message: str,
        level: str = "INFO"
    ) -> None:
        """Report activity through the application Logging screen."""

        app = App.get_running_app()

        if app is not None and app.root is not None:
            app.root.set_status(message, level)


Builder.load_file(str(Path(__file__).with_suffix(".kv")))
