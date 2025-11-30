from google.adk.plugins.logging_plugin import LoggingPlugin
import os

# Environment-based debug switch
DEBUG_ENABLED = os.getenv("ADK_DEBUG", "1") == "1"

# If debugging is enabled, load the ADK LoggingPlugin
# If disabled, set to None so calling code can easily skip it
logging_plugin = LoggingPlugin() if DEBUG_ENABLED else None

print(f"✅ logging_plugin.py loaded. DEBUG_ENABLED={DEBUG_ENABLED}")