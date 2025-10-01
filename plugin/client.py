from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

import sublime
from LSP.plugin import AbstractPlugin, DottedDict

from .constants import PACKAGE_NAME
from .log import log_warning
from .template import load_string_template
from .utils import decompress_buffer, rmtree_ex, sha256sum, simple_urlopen
from .version_manager import version_manager


class LspTyPlugin(AbstractPlugin):
    @classmethod
    def base_dir(cls) -> Path:
        return Path(cls.storage_path()) / PACKAGE_NAME

    @classmethod
    def versioned_server_dir(cls) -> Path:
        return cls.base_dir() / f"v{version_manager.server_version}"

    @classmethod
    def server_path(cls) -> Path:
        return cls.versioned_server_dir() / version_manager.THIS_TARBALL_BIN_PATH

    @classmethod
    def additional_variables(cls) -> dict[str, str] | None:
        return {
            "server_path": str(cls.server_path()),
        }

    @classmethod
    def needs_update_or_installation(cls) -> bool:
        return not cls.server_path().is_file()

    @classmethod
    def install_or_update(cls) -> None:
        rmtree_ex(cls.base_dir(), ignore_errors=True)

        data = simple_urlopen(version_manager.download_url)

        hash_actual = sha256sum(data)
        hash_golden = simple_urlopen(version_manager.download_hash_url).decode().partition(" ")[0]
        if hash_actual != hash_golden:
            raise ValueError(f"Mismatched downloaded file hash: {hash_actual} != {hash_golden}")

        decompress_buffer(
            io.BytesIO(data),
            filename=version_manager.THIS_TARBALL_NAME,
            dst_dir=cls.versioned_server_dir(),
        )

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
