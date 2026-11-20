"""
Created on Nov 19, 2026

@author: keith.chambers

Stream Configuration screen for EvalEDS.
"""

from pathlib import Path

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen


class StreamConfigurationScreen(Screen):
    """Configure stream ingestion and management."""

    pass


Builder.load_file(
    str(Path(__file__).with_suffix(".kv"))
)

