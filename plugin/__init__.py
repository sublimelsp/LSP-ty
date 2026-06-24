from __future__ import annotations

from .client import LspTyPlugin

__all__ = (
    # ST: core
    "plugin_loaded",
    "plugin_unloaded",
    # ...
    "LspTyPlugin",
)


def plugin_loaded() -> None:
    """Executed when this plugin is loaded."""
    LspTyPlugin.register()


def plugin_unloaded() -> None:
    """Executed when this plugin is unloaded."""
    LspTyPlugin.unregister()
