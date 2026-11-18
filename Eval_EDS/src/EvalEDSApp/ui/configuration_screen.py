"""Configuration screen for EvalEDS."""

import logging
from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from EvalEDSApp.config.app_constants import APP_NAMESPACE
from common.configuration import ConfigError
from EvalEDSApp.config import EvalEDSConfig
from EvalEDSApp.config import APP_NAMESPACE


logger = logging.getLogger(APP_NAMESPACE)


class ConfigurationScreen(Screen):
    """Presents application configuration controls and actions."""

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

        self.ids.url.text = config.url
        self.ids.port.text = str(config.port)
        self.ids.timeout.text = str(config.timeout)
        self.ids.retry_interval.text = str(config.retry_interval)


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

        try:
            return EvalEDSConfig(
                url=self.ids.url.text.strip(),
                port=int(self.ids.port.text.strip()),
                timeout=int(self.ids.timeout.text.strip()),
                retry_interval=int(
                    self.ids.retry_interval.text.strip()
                ),
            )

        except ValueError as exc:
            raise ValueError(
                "Port, timeout and retry interval must be integers."
            ) from exc

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
