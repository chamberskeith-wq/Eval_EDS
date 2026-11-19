"""Configuration screen for EvalEDS."""

from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, StringProperty

from common.configuration import ConfigError
from EvalEDSApp.config import EvalEDSConfig, APP_NAMESPACE

import logging
logger = logging.getLogger(APP_NAMESPACE)


class ConfigurationScreen(Screen):
    """Presents application configuration controls and actions."""

    has_changes = BooleanProperty(False)
    change_status = StringProperty("All changes saved")

    _saved_values = None

    # --------------------------------------------------------
    # Read displayed configuration values
    # --------------------------------------------------------
    def _read_form_values(self) -> tuple:
        """Return the current values displayed in the form."""

        return (
            self.ids.auto_connect.active
        )

    # --------------------------------------------------------
    # Update change state
    # --------------------------------------------------------
    def update_change_state(self, *args) -> None:
        """Compare displayed values against the saved baseline."""

        if self._saved_values is None:
            return

        current_values = self._read_form_values()

        self.has_changes = current_values != self._saved_values

        self.change_status = (
            "Unsaved changes"
            if self.has_changes
            else "All changes saved"
        )

    # --------------------------------------------------------
    # Establish saved baseline
    # --------------------------------------------------------
    def _set_saved_baseline(self) -> None:
        """Record the current form values as the saved baseline."""

        self._saved_values = self._read_form_values()

        self.has_changes = False
        self.change_status = "All changes saved"

    # --------------------------------------------------------
    # Load configuration into the screen
    # --------------------------------------------------------
    def load_from_config(self) -> None:
        """Populate the screen from the application's active config."""

        app = App.get_running_app()

        if app is None or not hasattr(app, "app_config"):
            return

        config = app.app_config

        self.ids.configuration_file.text = str(
            app.config_manager.config_file
        )

        self.ids.auto_connect.active = config.auto_connect

        # Establish the saved baseline.
        self._set_saved_baseline()
    
    # --------------------------------------------------------
    # Load configuration from file
    # --------------------------------------------------------
    def on_load_configuration(self) -> None:
        """Reload configuration from the YAML file."""

        app = App.get_running_app()

        try:
            config = app.config_manager.load()

        except ConfigError as exc:
            logger.exception("Unable to load application configuration")
            self._report_status(
                f"Unable to load configuration: {exc}",
                "ERROR",
            )
            return

        app.app_config = config
        self.load_from_config()

        self._report_status("Configuration loaded successfully.")

    # --------------------------------------------------------
    # Build candidate configuration
    # --------------------------------------------------------
    def _build_configuration(self) -> EvalEDSConfig:
        """Build a configuration object from the displayed values."""

        return EvalEDSConfig(
            auto_connect=bool(self.ids.auto_connect.active)  
        )

    # --------------------------------------------------------
    # Verify configuration
    # --------------------------------------------------------
    def on_verify_configuration(self) -> None:
        """Validate the values currently displayed on screen."""

        app = App.get_running_app()

        try:
            candidate = self._build_configuration()
            app.config_manager.validate(candidate)

        except (ValueError, ConfigError) as exc:
            logger.warning("Configuration verification failed: %s", exc)
            self._report_status(
                f"Configuration verification failed: {exc}",
                "ERROR",
            )
            return

        self._report_status("Configuration is valid.")

    # --------------------------------------------------------
    # Save configuration
    # --------------------------------------------------------
    def on_save_configuration(self) -> None:
        """Validate and persist the displayed configuration."""

        if not self.has_changes:
            self._report_status("No configuration changes to save.")
            return

        app = App.get_running_app()

        try:
            candidate = self._build_configuration()
            app.save_configuration(candidate)

        except (ValueError, ConfigError) as exc:
            logger.exception("Unable to save application configuration")
            self._report_status(
                f"Unable to save configuration: {exc}",
                "ERROR",
            )
            return

        self.load_from_config()
        self._report_status("Configuration saved successfully.")

    # --------------------------------------------------------
    # Status reporting
    # --------------------------------------------------------
    @staticmethod
    def _report_status(
        message: str,
        level: str = "INFO",
    ) -> None:
        """Send a message to the application's Status screen."""

        app = App.get_running_app()

        if app is not None and app.root is not None:
            app.root.set_status(message, level)



Builder.load_file(str(Path(__file__).with_suffix(".kv")))
