"""
Created on Nov 19, 2026

@author: keith.chambers

Combined settings screen for EvalEDS.

Provides separate tabs for the EDS connection profile and
application-wide settings. Each tab retains its own persistence
and change-tracking workflow.
"""

import logging
from datetime import datetime
from pathlib import Path
from threading import Thread

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    StringProperty,
)
from kivy.uix.screenmanager import Screen

from common.configuration import ConfigError, ConfigValidationError
from EvalEDSApp.config import APP_NAMESPACE, EvalEDSConfig
from common.eds import EDSConnectionProfile


logger = logging.getLogger(APP_NAMESPACE)


class SettingsScreen(Screen):
    """Manage the EDS connection profile and application settings."""

    # EDS profile state
    profile_has_changes = BooleanProperty(False)
    profile_change_status = StringProperty("All changes saved")
    connection_status = StringProperty("Not tested")
    profile_message = StringProperty("")
    profile_message_color = ListProperty([0.15, 0.5, 0.2, 1])

    # Application configuration state
    application_has_changes = BooleanProperty(False)
    application_change_status = StringProperty("All changes saved")

    # Connection summary
    connection_state = StringProperty("Not tested")
    connection_state_color = ListProperty([0.45, 0.45, 0.45, 1])
    connection_endpoint = StringProperty("Not configured")
    last_attempt = StringProperty("Never")
    last_result = StringProperty("No connection attempt recorded.")

    _saved_profile_values = None
    _saved_application_values = None
    _settings_initialized = False

    # ========================================================
    # EDS PROFILE TAB
    # ========================================================

    def _read_profile_values(self) -> tuple:
        return (
            self.ids.url.text.strip(),
            self.ids.port.text.strip(),
            self.ids.timeout.text.strip(),
            self.ids.retry_interval.text.strip(),
        )

    def update_profile_change_state(self, *args) -> None:
        if self._saved_profile_values is None:
            return

        self.profile_has_changes = (
            self._read_profile_values() != self._saved_profile_values
        )
        self.profile_change_status = (
            "Unsaved changes" if self.profile_has_changes
            else "All changes saved"
        )

        if self.profile_has_changes:
            self.profile_message = ""

    def _set_profile_saved_baseline(self) -> None:
        self._saved_profile_values = self._read_profile_values()
        self.profile_has_changes = False
        self.profile_change_status = "All changes saved"

    def load_from_profile(self) -> None:
        """Populate the EDS Profile tab from the active profile."""
        app = App.get_running_app()

        if app is None or not hasattr(app, "eds_connection_profile"):
            return

        profile = app.eds_connection_profile

        self.ids.connection_file.text = str(
            app.eds_connection_manager.config_file
        )
        self.ids.url.text = profile.url
        self.ids.port.text = str(profile.port)
        self.ids.timeout.text = str(profile.timeout)
        self.ids.retry_interval.text = str(profile.retry_interval)

        self.connection_status = "Not tested"
        self._set_profile_saved_baseline()

    def on_load_profile(self) -> None:
        """Reload the saved EDS connection profile."""
        app = App.get_running_app()

        try:
            profile = app.eds_connection_manager.load()

        except ConfigError as exc:
            logger.exception("Unable to load EDS connection profile")
            self._set_profile_message(
                f"Unable to load EDS profile: {exc}", "ERROR"
            )
            self._report_status(
                f"Unable to load EDS profile: {exc}", "ERROR"
            )
            return

        app.eds_connection_profile = profile
        app.eds_connection_service.set_active_profile(profile)

        self.load_from_profile()
        self.profile_message = ""
        self.connection_status = "Not tested"

        self._report_status(
            "EDS connection profile loaded successfully."
        )

    def _build_profile(self) -> EDSConnectionProfile:
        """Build a candidate profile from the displayed values."""
        try:
            port = int(self.ids.port.text.strip())
            timeout = int(self.ids.timeout.text.strip())
            retry_interval = int(self.ids.retry_interval.text.strip())

        except ValueError as exc:
            raise ValueError(
                "Port, timeout and retry interval must contain integers."
            ) from exc

        return EDSConnectionProfile(
            url=self.ids.url.text.strip(),
            port=port,
            timeout=timeout,
            retry_interval=retry_interval,
        )

    def _set_profile_message(
        self,
        message: str,
        level: str = "INFO"
    ) -> None:
        colors = {
            "INFO": [0.15, 0.35, 0.65, 1],
            "SUCCESS": [0.15, 0.5, 0.2, 1],
            "WARNING": [0.75, 0.45, 0.05, 1],
            "ERROR": [0.75, 0.15, 0.15, 1],
        }

        self.profile_message = message
        self.profile_message_color = colors.get(
            level, colors["INFO"]
        )

    def on_verify_profile(self) -> None:
        app = App.get_running_app()

        try:
            candidate = self._build_profile()
            app.eds_connection_manager.validate(candidate)

        except (ValueError, ConfigError) as exc:
            message = f"EDS Profile verification failed: {exc}"
            logger.warning(message)
            self._set_profile_message(message, "ERROR")
            self._report_status(message, "ERROR")
            return

        self._set_profile_message(
            "EDS connection profile is valid.", "SUCCESS"
        )
        self._report_status("EDS connection profile is valid.")

    def on_test_connection(self) -> None:
        """Test the displayed profile without saving or activating it."""
        app = App.get_running_app()

        if getattr(self, "_test_in_progress", False):
            return

        try:
            candidate = self._build_profile()

        except ValueError as exc:
            message = f"Invalid connection configuration: {exc}"
            self.connection_status = "Invalid configuration"
            self._set_profile_message(message, "ERROR")
            self._report_status(message, "ERROR")
            return

        try:
            app.eds_connection_manager.validate(candidate)

        except ConfigValidationError as exc:
            message = f"Invalid connection configuration: {exc}"
            self.connection_status = "Invalid configuration"
            self._set_profile_message(message, "ERROR")
            self._report_status(message, "ERROR")
            return

        endpoint = app.get_eds_endpoint(candidate)

        attempted_at = datetime.now().astimezone().strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )

        self._test_in_progress = True
        self.connection_status = "Connecting"

        self._set_profile_message(
            "Testing EDS connection...", "INFO"
        )

        app.update_connection_summary(
            state="Connecting",
            endpoint=endpoint,
            last_attempt=attempted_at,
            message="Testing EDS connection...",
        )

        self._report_status(
            f"Testing EDS connection at {endpoint}..."
        )

        self._connection_test_thread = Thread(
            target=self._connection_test_worker,
            args=(app, candidate, endpoint, attempted_at),
            daemon=True,
            name="EDS-ManualTest",
        )

        self._connection_test_thread.start()

    def _connection_test_worker(
        self,
        app,
        candidate,
        endpoint: str,
        attempted_at: str
    ) -> None:
        """Perform the HTTP connection test in the background."""
        try:
            result = app.eds_connection_service.test_connection(candidate)

        except Exception as exc:
            logger.exception(
                "Unexpected error during manual EDS connection test"
            )

            message = str(exc)

            Clock.schedule_once(
                lambda dt, msg=message:
                    self._complete_connection_test(
                        False, msg, endpoint, attempted_at
                    ),
                0,
            )
            return

        Clock.schedule_once(
            lambda dt, success=result.success, msg=result.message:
                self._complete_connection_test(
                    success, msg, endpoint, attempted_at
                ),
            0,
        )

    def _complete_connection_test(
        self,
        success: bool,
        message: str,
        endpoint: str,
        attempted_at: str
    ) -> None:
        """Update the profile tab after a connection test."""
        self._test_in_progress = False
        app = App.get_running_app()

        if success:
            self.connection_status = "Connected"
            screen_message = "EDS connection test successful."

            self._set_profile_message(screen_message, "SUCCESS")

            app.update_connection_summary(
                state="Connected",
                endpoint=endpoint,
                last_attempt=attempted_at,
                message=message,
            )

            self._report_status(screen_message)

        else:
            self.connection_status = "Connection failed"
            screen_message = (
                f"EDS connection test failed: {message}"
            )

            self._set_profile_message(screen_message, "ERROR")

            app.update_connection_summary(
                state="Disconnected",
                endpoint=endpoint,
                last_attempt=attempted_at,
                message=message,
            )

            self._report_status(screen_message, "ERROR")

    def on_save_profile(self) -> None:
        """Validate and save the displayed EDS connection profile."""
        if not self.profile_has_changes:
            self._set_profile_message(
                "No profile changes to save.", "INFO"
            )
            return

        app = App.get_running_app()

        try:
            candidate = self._build_profile()
            app.save_eds_connection_profile(candidate)

        except (ValueError, ConfigValidationError) as exc:
            message = f"Unable to save EDS profile: {exc}"
            logger.warning(message)
            self._set_profile_message(message, "ERROR")
            self._report_status(message, "ERROR")
            return

        except ConfigError as exc:
            message = f"Unable to save EDS profile: {exc}"
            logger.exception(message)
            self._set_profile_message(message, "ERROR")
            self._report_status(message, "ERROR")
            return

        self.load_from_profile()

        message = "EDS connection profile saved successfully."
        self._set_profile_message(message, "SUCCESS")
        self._report_status(message)

    # ========================================================
    # APPLICATION SETTINGS TAB
    # ========================================================

    def _read_application_values(self) -> tuple:
        return (self.ids.auto_connect.active,)

    def update_application_change_state(self, *args) -> None:
        if self._saved_application_values is None:
            return

        self.application_has_changes = (
            self._read_application_values()
            != self._saved_application_values
        )

        self.application_change_status = (
            "Unsaved changes" if self.application_has_changes
            else "All changes saved"
        )

    def _set_application_saved_baseline(self) -> None:
        self._saved_application_values = (
            self._read_application_values()
        )

        self.application_has_changes = False
        self.application_change_status = "All changes saved"

    def load_from_config(self) -> None:
        """Populate the Application Settings tab from active config."""
        app = App.get_running_app()

        if app is None or not hasattr(app, "app_config"):
            return

        self.ids.configuration_file.text = str(
            app.config_manager.config_file
        )

        self.ids.auto_connect.active = app.app_config.auto_connect

        self._set_application_saved_baseline()

    def on_load_configuration(self) -> None:
        """Reload application configuration from its YAML file."""
        app = App.get_running_app()

        try:
            config = app.config_manager.load()

        except ConfigError as exc:
            logger.exception(
                "Unable to load application configuration"
            )
            self._report_status(
                f"Unable to load configuration: {exc}", "ERROR"
            )
            return

        app.app_config = config
        self.load_from_config()

        self._report_status("Configuration loaded successfully.")

    def _build_configuration(self) -> EvalEDSConfig:
        return EvalEDSConfig(
            auto_connect=bool(self.ids.auto_connect.active)
        )

    def on_verify_configuration(self) -> None:
        app = App.get_running_app()

        try:
            candidate = self._build_configuration()
            app.config_manager.validate(candidate)

        except (ValueError, ConfigError) as exc:
            logger.warning(
                "Configuration verification failed: %s", exc
            )
            self._report_status(
                f"Configuration verification failed: {exc}",
                "ERROR"
            )
            return

        self._report_status(
            "Application configuration is valid."
        )

    def on_save_configuration(self) -> None:
        if not self.application_has_changes:
            self._report_status(
                "No application configuration changes to save."
            )
            return

        app = App.get_running_app()

        try:
            candidate = self._build_configuration()
            app.save_configuration(candidate)

        except (ValueError, ConfigError) as exc:
            logger.exception(
                "Unable to save application configuration"
            )
            self._report_status(
                f"Unable to save application configuration: {exc}",
                "ERROR"
            )
            return

        self.load_from_config()

        self._report_status(
            "Application configuration saved successfully."
        )

    # ========================================================
    # CONNECTION SUMMARY
    # ========================================================

    def update_connection_status(
        self,
        state: str,
        endpoint: str = "Not configured",
        last_attempt: str = "Never",
        message: str = "No connection attempt recorded.",
    ) -> None:
        """Update the connection summary shown on the EDS Profile tab."""
        self.connection_state = state
        self.connection_endpoint = endpoint
        self.last_attempt = last_attempt
        self.last_result = message

        if state == "Connected":
            self.connection_state_color = [0.1, 0.55, 0.2, 1]

        elif state == "Connecting":
            self.connection_state_color = [0.85, 0.55, 0.05, 1]

        elif state == "Disconnected":
            self.connection_state_color = [0.8, 0.15, 0.15, 1]

        else:
            self.connection_state_color = [0.45, 0.45, 0.45, 1]

    # ========================================================
    # SHARED STATUS REPORTING
    # ========================================================
    @staticmethod
    def _report_status(
        message: str,
        level: str = "INFO"
    ) -> None:
        app = App.get_running_app()

        if app is not None and app.root is not None:
            app.root.set_status(message, level)

    def on_enter(self, *args):
        """Initialize settings when the screen is first opened."""
    
        if self._settings_initialized:
            return
    
        self.load_from_profile()
        self.load_from_config()
    
        self._settings_initialized = True

Builder.load_file(str(Path(__file__).with_suffix(".kv")))

