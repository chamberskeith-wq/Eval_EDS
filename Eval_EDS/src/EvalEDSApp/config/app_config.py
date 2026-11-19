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

from common.configuration import ConfigValidationError

from .app_constants import (
    DEFAULT_AUTO_CONNECT,
)


@dataclass
class EvalEDSConfig:
    """
    EvalEDS application configuration.

    Common's ConfigManager handles persistence.
    This class defines the application-specific configuration.
    """

    # --------------------------------------------------------
    # app configuration
    # --------------------------------------------------------

    auto_connect: bool = DEFAULT_AUTO_CONNECT
    
    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def validate(self) -> None:
        """
        Validate application configuration.

        Raises:
            ConfigValidationError: Invalid configuration values.
        """

        # ---- AUTO_CONNECT ----

        if not isinstance(self.auto_connect, bool):
            raise ConfigValidationError(
                "Auto-connect must be a boolean value."
            )
