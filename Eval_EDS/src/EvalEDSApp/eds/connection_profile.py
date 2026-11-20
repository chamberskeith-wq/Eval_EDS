"""
Created on Nov 18, 2026

@author: keith.chambers
EDS connection profile.

Defines the connection settings used by EvalEDS
to communicate with one AVEVA Edge Data Store instance.
"""

from dataclasses import dataclass
from urllib.parse import urlsplit
import logging

from common.configuration import ConfigValidationError

from EvalEDSApp.config.app_constants import (
    DEFAULT_PORT,
    DEFAULT_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_INTERVAL,
    APP_NAMESPACE
)

logger = logging.getLogger(APP_NAMESPACE)

@dataclass
class EDSConnectionProfile:
    """
    Connection settings for the active EDS instance.

    Persistence is handled by Common's ConfigManager.
    Credentials are deliberately excluded and handled
    separately by Common's SecretManager.
    """

    url: str = DEFAULT_URL
    port: int = DEFAULT_PORT
    timeout: int = DEFAULT_TIMEOUT
    retry_interval: int = DEFAULT_RETRY_INTERVAL

    def validate(self) -> None:
        """
        Validate the EDS connection settings.

        Raises:
            ConfigValidationError: If a setting is invalid.
        """

        # URL
        if not isinstance(self.url, str) or not self.url.strip():
            raise ConfigValidationError(
                "A valid EDS URL must be provided."
            )

        parsed_url = urlsplit(self.url.strip())

        if (
            parsed_url.scheme not in ("http", "https")
            or not parsed_url.hostname
            or parsed_url.path not in ("", "/")
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise ConfigValidationError(
                "EDS URL must be a valid HTTP or HTTPS base URL "
                "without a path, query or fragment."
            )

        # PORT
        if (
            not isinstance(self.port, int)
            or isinstance(self.port, bool)
            or not 1 <= self.port <= 65535
        ):
            raise ConfigValidationError(
                "Port must be an integer between 1 and 65535."
            )

        # TIMEOUT
        if (
            not isinstance(self.timeout, int)
            or isinstance(self.timeout, bool)
            or self.timeout <= 0
        ):
            raise ConfigValidationError(
                "Timeout must be a positive integer."
            )

        # RETRY INTERVAL
        if (
            not isinstance(self.retry_interval, int)
            or isinstance(self.retry_interval, bool)
            or self.retry_interval <= 0
        ):
            raise ConfigValidationError(
                "Retry interval must be a positive integer."
            )
