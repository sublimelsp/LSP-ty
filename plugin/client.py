from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import sublime
from LSP.plugin import AbstractPlugin, ClientConfig, DottedDict
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

    # ----- #
    # hooks #
    # ----- #

    @override
    def on_settings_changed(self, settings: DottedDict) -> None:
        super().on_settings_changed(settings)

        self.update_status_bar_text()

    @override
    def on_workspace_configuration(self, params: Any, configuration: Any) -> Any:
        if not (session := self.weaksession()):
            return configuration
        if not isinstance(configuration, dict):
            return configuration

        # Don't override if the user already set an interpreter explicitly
        if configuration.get("interpreter"):
            return configuration

        venv_dir = self._find_venv_dir(session)
        if venv_dir:
            python = venv_dir / "Scripts" / "python.exe" if sys.platform == "win32" else venv_dir / "bin" / "python"
            if python.is_file():
                configuration["interpreter"] = [str(python)]

        return configuration

    # -------------- #
    # custom methods #
    # -------------- #

    def _find_venv_dir(self, session: Any) -> Path | None:
        """Find a virtual environment directory, checking the ty.venvDir setting first, then auto-detecting."""
        workspace_folders = session.get_workspace_folders()
        if not workspace_folders:
            return None
        # Use the first workspace folder as the project root
        project_dir = Path(workspace_folders[0].path)

        # 1. Check explicit setting
        venv_dir_setting = session.config.settings.get("ty.venvDir") or ""
        if venv_dir_setting:
            path = Path(venv_dir_setting)
            if not path.is_absolute():
                path = project_dir / path
            if self._is_venv(path):
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
