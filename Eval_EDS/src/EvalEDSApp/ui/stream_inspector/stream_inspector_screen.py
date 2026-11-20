"""
Created on Nov 19, 2026

@author: keith.chambers
Stream Inspector screen for EvalEDS.
"""

from pathlib import Path

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen


class StreamInspectorScreen(Screen):
    """Browse and inspect streams available in EDS."""

    pass


Builder.load_file(
    str(Path(__file__).with_suffix(".kv"))
)
