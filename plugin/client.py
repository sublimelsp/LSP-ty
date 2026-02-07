from __future__ import annotations

import os
from typing import Any

import sublime
from LSP.plugin import AbstractPlugin, DottedDict

from .constants import PACKAGE_NAME
from .log import log_warning
from .template import load_string_template
from .version_manager import version_manager


class LspTyPlugin(AbstractPlugin):
    @classmethod
    def name(cls) -> str:
        return PACKAGE_NAME

    @classmethod
    def configuration(cls) -> tuple[sublime.Settings, str]:
        basename = f"{cls.name()}.sublime-settings"
        filepath = f"Packages/{cls.name()}/{basename}"
        return sublime.load_settings(basename), filepath

    @classmethod
    def additional_variables(cls) -> dict[str, str] | None:
        return {
            "server_path": str(version_manager.server_path),
        }

    @classmethod
    def needs_update_or_installation(cls) -> bool:
        return not version_manager.is_installed

    @classmethod
    def install_or_update(cls) -> None:
        version_manager.install_server()

    @classmethod
    def should_ignore(cls, view: sublime.View) -> bool:
        return bool(
            # SublimeREPL views
            view.settings().get("repl")
            # syntax test files
            or os.path.basename(view.file_name() or "").startswith("syntax_test")
        )

    # ----- #
    # hooks #
    # ----- #

    def on_settings_changed(self, settings: DottedDict) -> None:
        super().on_settings_changed(settings)

        self.update_status_bar_text()

    # -------------- #
    # custom methods #
    # -------------- #

    def update_status_bar_text(self, extra_variables: dict[str, Any] | None = None) -> None:
        if not (session := self.weaksession()):
            return

        variables: dict[str, Any] = {
            "server_version": version_manager.server_version,
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
