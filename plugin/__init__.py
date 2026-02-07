from __future__ import annotations

from LSP.plugin import register_plugin, unregister_plugin

from .client import LspTyPlugin
from .constants import SERVER_VERSION
from .version_manager import version_manager

__all__ = (
    # ST: core
    "plugin_loaded",
    "plugin_unloaded",
    # ...
    "LspTyPlugin",
)


def plugin_loaded() -> None:
    """Executed when this plugin is loaded."""
    register_plugin(LspTyPlugin)

    version_manager.client_cls = LspTyPlugin
    version_manager.server_version = SERVER_VERSION


def plugin_unloaded() -> None:
    """Executed when this plugin is unloaded."""
    unregister_plugin(LspTyPlugin)
