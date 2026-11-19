'''
Created on Aug 25, 2025

@author: keith.chambers
'''

# -----------------------------
# imports
# -----------------------------
# Common services
from common.configuration import ConfigManager, SecretManager, ConfigError, ConfigSecretError
from datetime import datetime

# EvalEDS package imports
from EvalEDSApp.eds import (
    EDSConnectionProfile,
)
from EvalEDSApp.ui import (
    StatusScreen,  
    InspectorScreen, 
    ConfigurationScreen,
    EDSConnectionScreen,
)
from EvalEDSApp.config import (
    EvalEDSConfig,
    APP_NAME,
    APP_NAMESPACE,
    CONFIG_FILE_NAME,
    CONFIG_FILE_PATH,
    EDS_CONNECTION_FILE_NAME,
    EDS_USERNAME_NAME,
    EDS_PASSWORD_NAME,
    EDS_USERNAME_ENV,
    EDS_PASSWORD_ENV
)

from pathlib import Path
from threading import Thread
# -----------------------------
# Configure logging
# -----------------------------
from common.logging import configure_base_logging, enforce_library_levels
configure_base_logging()

import logging
logger = logging.getLogger(APP_NAMESPACE)


# Kivy imports
from kivy.app import App
from kivy.utils import colormap 
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.clock import Clock

# the screen procedures need to be imported even though they are not directly referenced 
from EvalEDSApp.ui import StatusScreen,  InspectorScreen, ConfigurationScreen
from EvalEDSApp.eds import EDSConnectionProfile, EDSConnectionService
from EvalEDSApp.config import EvalEDSConfig

# from AskMeApp.ui.settings_screen import SettingsScreen
# from AskMeApp.ui.context_screen import ContextScreen
# ============================================================
# EvalEDS - Main Screen
# ============================================================

class EvalEDSScreen(BoxLayout):
    """
    Main application layout.
    """

    def set_status(self, message, level="INFO"):
        """Append a message to the Status screen."""
    
        status_screen = self.ids.screen_manager.get_screen("status")
        status_screen.add_message(message, level)

    # --------------------------------------------------------
    # Application status
    # --------------------------------------------------------

    def set_application_status(self, message: str):
        """Update the bottom application status strip."""

        label = self.ids.get("application_status")

        if label is not None:
            label.text = message

  
#===============================================================================
# EvalEDS - kivy app
#===============================================================================
class EvalEDSApp(App):
    """
    EvalEDS Kivy application.

    Initializes Common configuration and secret services
    and makes them available to application components.
    """

    # Explicitly identify the KV file.
    kv_file = str(
        Path(__file__).resolve().parent / "EvalEDS.kv"
    )

    # Define a palette of common colors.
    colors = colormap
    
    #===========================================================================
    # build
    #===========================================================================
    def build(self):
        """
        Build the application UI.
        """
        
        self.main_screen = EvalEDSScreen()

        return self.main_screen
    
    #===========================================================================
    # on_start
    #===========================================================================
    def on_start(self):
        """
        Initialize application services after startup.
        """

        #App is now live — UI exists
        
        #reset logger level for noisy libs
        enforce_library_levels(APP_NAMESPACE)

        logger.info("Starting %s", APP_NAME)

        try:
            self.initialize_configuration()
            self.initialize_secrets()
            self.initialize_eds_connection_profile()
            self.initialize_eds_connection_service()
            
            configuration_screen = (
                self.root.ids.screen_manager.get_screen("configuration")
            )
            configuration_screen.load_from_config() 
            
            connection_screen = (
                self.root.ids.screen_manager.get_screen("eds_connection")
            )
            connection_screen.load_from_profile() 

            # Initialize the Status screen connection summary.
            self.update_connection_summary(
                state="Not tested",
                message="No connection attempt recorded."
            )

            self.root.set_status(
                "application services initiaitlized."
            )

            self.root.set_application_status("Ready")
            
            # Start automatic EDS connection if enabled.
            self.start_auto_connect()
            
        except ConfigError:

            logger.exception(
                "Application configuration initialization failed"
            )

            self.root.set_status(
                "Application configuration initialization failed.",
                "ERROR"
            )

            self.root.set_application_status(
                "Startup error"
            )

            raise

        logger.info("%s started successfully", APP_NAME)

    # --------------------------------------------------------
    # Connection status helpers
    # --------------------------------------------------------
    def get_eds_endpoint(self, profile=None) -> str:
        """Return the specified or active EDS endpoint."""

        if profile is None:
            profile = self.eds_connection_profile

        return f"{profile.url.rstrip('/')}:{profile.port}"
    
    def update_connection_summary(
        self,
        state: str,
        message: str,
        last_attempt: str | None = None,
        endpoint: str | None = None
    ):
        """Update the Status screen connection summary."""

        status_screen = self.root.ids.screen_manager.get_screen(
            "status"
        )

        status_screen.update_connection_status(
            state=state,
            endpoint=endpoint or self.get_eds_endpoint(),
            last_attempt=last_attempt or "Never",
            message=message
        )
        
    # --------------------------------------------------------
    # Start automatic EDS connection
    # --------------------------------------------------------
    def start_auto_connect(self):
        """
        Start an automatic EDS connection if enabled.
        """

        if not self.app_config.auto_connect:
            logger.info("EDS auto-connect is disabled")

            self.root.set_status(
                "EDS auto-connect is disabled."
            )

            self.update_connection_summary(
                state="Not tested",
                message="Automatic connection is disabled."
            )

            return

        logger.info("Starting automatic EDS connection")

        # Record the attempt time.
        self._connection_attempt_time = (
            datetime.now().astimezone().strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
        )

        self.update_connection_summary(
            state="Connecting",
            message="Attempting to connect to EDS...",
            last_attempt=self._connection_attempt_time
        )

        self.root.set_status(
            "Attempting automatic EDS connection..."
        )

        self.root.set_application_status(
            "Connecting to EDS..."
        )

        self._connection_thread = Thread(
            target=self._auto_connect_worker,
            daemon=True,
            name="EDS-AutoConnect"
        )

        self._connection_thread.start()
        
    # --------------------------------------------------------
    # Auto Connect background worker
    # --------------------------------------------------------

    def _auto_connect_worker(self):
        """
        Perform the EDS connection test in the background.
        """

        try:
            result = self.eds_connection_service.test_connection()

        except Exception as exc:
            logger.exception("Unexpected error during EDS auto-connect")

            message = str(exc)

            Clock.schedule_once(
                lambda dt, msg=message:
                    self._complete_auto_connect(False, msg),
                0
            )
            return

        Clock.schedule_once(
            lambda dt, success=result.success, msg=result.message:
                self._complete_auto_connect(success, msg),
            0
        )

    # --------------------------------------------------------
    # Complete Auto Connect
    # --------------------------------------------------------

    def _complete_auto_connect(
        self,
        success: bool,
        message: str
    ):
        """
        Update the application UI after the connection test.
        """

        if success:
            logger.info("EDS auto-connect successful")

            self.update_connection_summary(
                state="Connected",
                message=message,
                last_attempt=self._connection_attempt_time
            )

            self.root.set_status(
                "EDS auto-connect successful."
            )

            self.root.set_application_status(
                "EDS Connected"
            )

        else:
            logger.warning(
                "EDS auto-connect failed: %s",
                message
            )

            self.update_connection_summary(
                state="Disconnected",
                message=message,
                last_attempt=self._connection_attempt_time
            )

            self.root.set_status(
                f"EDS auto-connect failed: {message}",
                "ERROR"
            )

            self.root.set_application_status(
                "EDS Connection Failed"
            )
                    
    # --------------------------------------------------------
    # Initialize configuration
    # --------------------------------------------------------
    def initialize_configuration(self):
        """
        Initialize and load application configuration.
        """

        self.config_manager = ConfigManager(
            config_type=EvalEDSConfig,
            config_file_name = CONFIG_FILE_NAME,
            config_file_path = CONFIG_FILE_PATH
        )

        # Load existing configuration or create defaults.
        self.app_config = self.config_manager.load(
            create_if_missing= True
        )

        logger.info("Application configuration initialized")

    # --------------------------------------------------------
    # Initialize EDS connection profile
    # --------------------------------------------------------
    def initialize_eds_connection_profile(self):
        """
        Initialize and load the EDS connection profile.

        The connection profile is persisted separately
        from the general application configuration.
        """
      
        self.eds_connection_manager = ConfigManager(
            config_type=EDSConnectionProfile,
            config_file_name=EDS_CONNECTION_FILE_NAME,
            config_file_path=CONFIG_FILE_PATH
        )
       
        self.eds_connection_profile = (
            self.eds_connection_manager.load(
                create_if_missing=True
            )
        )
        
        logger.info("EDS connection profile initialized")
        
    # --------------------------------------------------------
    # Initialize EDS connection service
    # --------------------------------------------------------
    def initialize_eds_connection_service(self):
        """
        Initialize the EDS connection service.

        The loaded connection profile becomes the active
        profile used for normal EDS operations.
        """

        self.eds_connection_service = EDSConnectionService()

        self.eds_connection_service.set_active_profile(
            self.eds_connection_profile
        )

        logger.info("EDS connection service initialized")    

    # --------------------------------------------------------
    # Initialize secrets
    # --------------------------------------------------------
    def initialize_secrets(self):
        """
        Initialize application secret management.

        Secrets are retrieved independently from configuration.
        """

        self.secret_manager = SecretManager(APP_NAME)

        try:
            self.eds_username = self.secret_manager.get_secret(
                EDS_USERNAME_NAME,
                EDS_USERNAME_ENV
            )

            self.eds_password = self.secret_manager.get_secret(
                EDS_PASSWORD_NAME,
                EDS_PASSWORD_ENV
            )

        except ConfigSecretError:
            logger.exception("Unable to initialize application secrets")
            raise

        logger.info("Secret manager initialized")

        # Do not log secret values.

    # --------------------------------------------------------
    # Save configuration
    # --------------------------------------------------------
    def save_configuration(self, config=None) -> None:
        """
        Save application configuration.
    
        The active configuration is updated only after
        the configuration manager successfully saves it.
        """
    
        if config is None:
            config = self.app_config
    
        self.config_manager.save(config)
    
        self.app_config = config

    # --------------------------------------------------------
    # Save EDS connection profile
    # --------------------------------------------------------

    def save_eds_connection_profile(self, profile=None):
        """
        Save the EDS connection profile.

        Update the active profile only after successful
        persistence.
        """

        if profile is None:
            profile = self.eds_connection_profile

        # Validate before saving.
        self.eds_connection_manager.validate(profile)

        # Persist the profile.
        self.eds_connection_manager.save(profile)

        # Update the application's active profile.
        self.eds_connection_profile = profile

        # Update the connection service.
        self.eds_connection_service.set_active_profile(profile)

        logger.info("EDS connection profile saved")
        
    # --------------------------------------------------------
    # Update secret
    # --------------------------------------------------------
    def update_secret(self, secret_name: str, value: str):
        """
        Store an application secret.
        """

        self.secret_manager.set_secret(
            secret_name,
            value
        )

# ============================================================
# Application Entry Point
# ============================================================        
 
if __name__ == '__main__':
    EvalEDSApp().run()