"""
conftest.py — Mock heavy dependencies before test collection.
Prevents ModuleNotFoundError for nicegui and other UI-only packages.
"""

import sys
from unittest.mock import MagicMock

# --- Mock nicegui before any module imports it ---
mock_nicegui = MagicMock()
mock_nicegui.app.storage.user = {}
sys.modules["nicegui"] = mock_nicegui
sys.modules["nicegui.app"] = mock_nicegui.app
