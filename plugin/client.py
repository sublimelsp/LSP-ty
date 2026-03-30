from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import sublime
from LSP.plugin import AbstractPlugin, ClientConfig, DottedDict, WorkspaceFolder
from typing_extensions import override

from .constants import PACKAGE_NAME
from .log import log_warning
from .template import load_string_template
from .version_manager import version_manager


class LspTyPlugin(AbstractPlugin):
    @override
    @classmethod
    def name(cls) -> str:
        return PACKAGE_NAME

    @override
    @classmethod
    def configuration(cls) -> tuple[sublime.Settings, str]:
        basename = f"{cls.name()}.sublime-settings"
        filepath = f"Packages/{cls.name()}/{basename}"
        return sublime.load_settings(basename), filepath

    @override
    @classmethod
    def additional_variables(cls) -> dict[str, str] | None:
        return {
            "server_path": str(version_manager.server_path),
        }

    @override
    @classmethod
    def needs_update_or_installation(cls) -> bool:
        return not version_manager.is_installed

    @override
    @classmethod
    def install_or_update(cls) -> None:
        version_manager.install_server()

    @override
    @classmethod
    def is_applicable(cls, view: sublime.View, config: ClientConfig) -> bool:
        return bool(
            super().is_applicable(view, config)
            # REPL views (https://github.com/sublimelsp/LSP-pyright/issues/343)
            and not view.settings().get("repl")
        )

    @override
    @classmethod
    def on_pre_start(
        cls,
        window: sublime.Window,
        initiating_view: sublime.View,
        workspace_folders: list[WorkspaceFolder],
        configuration: ClientConfig,
    ) -> str | None:
        venv_dir = cls._find_venv_dir(workspace_folders, configuration)
        if venv_dir:
            configuration.env["VIRTUAL_ENV"] = str(venv_dir)
        return None

    # ----- #
    # hooks #
    # ----- #

    @override
    def on_settings_changed(self, settings: DottedDict) -> None:
        super().on_settings_changed(settings)

        # Remove our custom setting so it doesn't get sent to the ty server
        settings.remove("ty.venvDir")

        self.update_status_bar_text()

    # -------------- #
    # custom methods #
    # -------------- #

    @classmethod
    def _find_venv_dir(
        cls, workspace_folders: list[WorkspaceFolder], configuration: ClientConfig
    ) -> Path | None:
        """Find a virtual environment directory, checking the ty.venvDir setting first, then auto-detecting."""
        if not workspace_folders:
            return None
        project_dir = Path(workspace_folders[0].path)

        # 1. Check explicit setting
        venv_dir_setting = configuration.settings.get("ty.venvDir") or ""
        if venv_dir_setting:
            path = Path(venv_dir_setting)
            if not path.is_absolute():
                path = project_dir / path
            if cls._is_venv(path):
                return path
            return None

    @staticmethod
    def _is_venv(path: Path) -> bool:
        """Check if a directory looks like a Python virtual environment."""
        return path.is_dir() and (path / "pyvenv.cfg").is_file()

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
