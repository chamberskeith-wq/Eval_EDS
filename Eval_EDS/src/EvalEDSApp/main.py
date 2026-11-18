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

#application configuration
from EvalEDSApp.config import EvalEDSConfig

from EvalEDSApp.config import (
    APP_NAME,
    APP_NAMESPACE,
    CONFIG_FILE_NAME,
    CONFIG_FILE_PATH,
    EDS_USERNAME_NAME,
    EDS_PASSWORD_NAME,
    EDS_USERNAME_ENV,
    EDS_PASSWORD_ENV
)

from pathlib import Path
# -----------------------------
# Configure logging
# -----------------------------
from common.logging import configure_base_logging, enforce_library_levels
from flatbuffers.builder import Builder
configure_base_logging()

import logging
logger = logging.getLogger(APP_NAMESPACE)


# Kivy imports
from kivy.app import App
from kivy.utils import colormap 
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

# the screen procedures need to be imported even though they are not directly referenced 
from EvalEDSApp.ui import StatusScreen,  InspectorScreen, ConfigurationScreen

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
            
            configuration_screen = (
                self.root.ids.screen_manager.get_screen("configuration")
            )
            configuration_screen.load_from_config() 
            
            self.root.set_status(
                "application services initiaitlized."
            )

            self.root.set_application_status("Ready")

            inspector = self.root.ids.screen_manager.get_screen("inspector")
            inspector.set_text(
                "Select an item to inspect. "
                "Historian browsing will be added in a later stage."
         )
            
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