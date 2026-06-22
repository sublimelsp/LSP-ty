from __future__ import annotations

from typing import Any

from LSP.plugin import ClientNotification, LspPlugin, OnPreStartContext

from .constants import SERVER_VERSION
from .log import log_warning
from .template import load_string_template
from .version_manager import VersionManager


class LspTyPlugin(LspPlugin):
    version_manager: VersionManager | None = None

    @classmethod
    def on_pre_start_async(cls, context: OnPreStartContext) -> None:
        server_path = context.configuration.root_settings.get("server_path")
        if not server_path or server_path == "auto":
            cls.version_manager = VersionManager(cls.plugin_storage_path, SERVER_VERSION)
            cls.version_manager.install_server()
            server_path = str(cls.version_manager.server_path)

        context.variables.update({
            "server_path": server_path,
        })

    # ----- #
    # hooks #
    # ----- #

    def on_pre_send_notification_async(self, notification: ClientNotification) -> None:
        if notification["method"] == "workspace/didChangeConfiguration":
            self.update_status_bar_text()
            return

    # -------------- #
    # custom methods #
    # -------------- #

    def update_status_bar_text(self, extra_variables: dict[str, Any] | None = None) -> None:
        if not (session := self.weaksession()):
            return

        variables: dict[str, Any] = {
            "server_version": self.version_manager.server_version if self.version_manager else None,
        }

        if extra_variables:
            variables.update(extra_variables)

        rendered_text = ""
        if template_text := str(session.config.settings.get("statusText") or ""):
            try:
                rendered_text = load_string_template(template_text).render(variables)
            except Exception as e:
                log_warning(f'Invalid "statusText" template: {e}')
        session.set_config_status_async(rendered_text)
