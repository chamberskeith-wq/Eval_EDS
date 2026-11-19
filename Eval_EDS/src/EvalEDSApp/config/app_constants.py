"""
Created on Sep 10, 2025

@author: keith.chambers

EvalEDS application constants.
"""

import os

# ============================================================
# Application identification
# ============================================================
APP_NAME = "EvalEDS"
APP_NAMESPACE = APP_NAME + "App"


# ============================================================
# Configuration and profile file
# ============================================================
CONFIG_FILE_NAME = "EvalEDS.yml"
CONFIG_FILE_PATH = os.path.abspath("./")
EDS_CONNECTION_FILE_NAME = "EDSConnection.yml"

# ============================================================
# Default configuration
# ============================================================
DEFAULT_AUTO_CONNECT = False

# ============================================================
# Default profile
# ============================================================
DEFAULT_PORT = 5590
DEFAULT_URL = "http://localhost"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_INTERVAL = 5

# ============================================================
# Application secrets
# ============================================================

EDS_USERNAME_NAME = "eds_username"
EDS_PASSWORD_NAME = "eds_password"

EDS_USERNAME_ENV = "EDS_USERNAME"
EDS_PASSWORD_ENV = "EDS_PASSWORD"

