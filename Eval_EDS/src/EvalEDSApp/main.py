'''
Created on Aug 25, 2025

@author: keith.chambers
'''

# -----------------------------
# imports
# -----------------------------
# Common services
from common.configuration.manager import ConfigManager
from common.configuration.secrets import SecretManager
from common.configuration.exceptions import ConfigError, ConfigSecretError

#application configuration
from EvalEDSApp.config.app_config import EvalEDSConfig

from EvalEDSApp.config.app_constants import (
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
from common.logging.my_logging import configure_base_logging, enforce_library_levels
configure_base_logging()

import logging
logger = logging.getLogger(APP_NAMESPACE)


# Kivy imports
from kivy.app import App
from kivy.utils import colormap 

# the screen procedures need to be imported even though they are not directly referenced 
# from AskMeApp.ui.query_screen import QueryScreen
# from AskMeApp.ui.settings_screen import SettingsScreen
# from AskMeApp.ui.context_screen import ContextScreen

#===============================================================================
# EvalEDS - kivy app
#===============================================================================
class EvalEDSApp(App):
    """
    EvalEDS Kivy application.

    Initializes Common configuration and secret services
    and makes them available to application components.
    """


    # Define a palette of common colors.
    colors = colormap
    
    #===========================================================================
    # build
    #===========================================================================
    def build(self):
        """
        Build the application UI.
        """

           
        #3 Let Kivy load KV + root widget
        return super().build()
    
    #===========================================================================
    # on_start
    #===========================================================================
    def on_start(self):
        """
        Initialize application services after startup.
        """

        #App is now live — UI exists
        
        #reset logger level for noisy libs
        enforce_library_levels()

        logger.info("Starting %s", APP_NAME)

        try:
            self.initialize_configuration()
            self.initialize_secrets()

        except ConfigError:
            logger.exception(
                "Application configuration initialization failed"
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

        config_path = (
            Path(CONFIG_FILE_PATH) / CONFIG_FILE_NAME
        )

        self.config_manager = ConfigManager(
            config_type=EvalEDSConfig,
            config_file=config_path
        )

        # Load existing configuration or create defaults.
        self.app_config = self.config_manager.create_default()

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

    def save_configuration(self):
        """
        Save current application configuration.
        """

        self.config_manager.save(self.app_config)

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

        
 
if __name__ == '__main__':
    EvalEDSApp().run()