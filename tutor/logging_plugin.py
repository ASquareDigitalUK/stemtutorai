from google.adk.plugins.logging_plugin import LoggingPlugin
import os
from tutor.config import settings

# Environment-based debug switch
DEBUG_ENABLED = settings.ADK_DEBUG

# If debugging is enabled, load the ADK LoggingPlugin
# If disabled, set to None so calling code can easily skip it
logging_plugin = LoggingPlugin() if DEBUG_ENABLED else None

print(f"✅ logging_plugin.py loaded. DEBUG_ENABLED={DEBUG_ENABLED}")