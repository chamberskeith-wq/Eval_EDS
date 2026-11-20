
"""EvalEDS user-interface screens."""

from .stream_inspector.stream_inspector_screen import StreamInspectorScreen
from .stream_configuration.stream_configuration_screen import StreamConfigurationScreen
from .eds_administration.eds_administration_screen import EDSAdministrationScreen
from .logging.logging_screen import LoggingScreen
from .settings.settings_screen import SettingsScreen


__all__ = [
    "StreamInspectorScreen",
    "StreamConfigurationScreen"
    "EDSAdministrationScreen",
    "LoggingScreen",
    "SettingsScreen",
]
