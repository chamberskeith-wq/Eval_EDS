'''
Created on Sep 10, 2025

@author: keith.chambers
'''
"""
EvalEDS application configuration model.

Defines application-specific configuration fields,
default values and validation rules.
"""

from dataclasses import dataclass
from pathlib import Path

from common.configuration.exceptions import ConfigValidationError

from .app_constants import (
    DEFAULT_PORT,
    DEFAULT_URL
)


@dataclass
class EvalEDSConfig:
    """
    EvalEDS application configuration.

    Common's ConfigManager handles persistence.
    This class defines the application-specific configuration.
    """

    # --------------------------------------------------------
    # AVEVA Edge Data Store connection
    # --------------------------------------------------------

    port: int = 5590
    url: str = ""

    # --------------------------------------------------------
    # Connection settings
    # --------------------------------------------------------

    timeout: int = 30
    retry_interval: int = 5

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def validate(self) -> None:
        """
        Validate application configuration.

        Raises:
            ConfigValidationError: Invalid configuration values.
        """

        # ---- PORT ----

        if (
            not isinstance(self.port, int)
            or isinstance(self.port, bool)
            or not 1 <= self.port <= 65535
        ):
            raise ConfigValidationError(
                "Port must be an integer between 1 and 65535"
            )

        # ---- URL ----

        if not isinstance(self.url, str) or not self.url.strip():
            raise ConfigValidationError(
                "A valid URL must be provided"
            )

        # ---- TIMEOUT ----

        if (
            not isinstance(self.timeout, int)
            or isinstance(self.timeout, bool)
            or self.timeout <= 0
        ):
            raise ConfigValidationError(
                "Timeout must be a positive integer"
            )

        # ---- RETRY INTERVAL ----

        if (
            not isinstance(self.retry_interval, int)
            or isinstance(self.retry_interval, bool)
            or self.retry_interval <= 0
        ):
            raise ConfigValidationError(
                "Retry interval must be a positive integer"
            )
