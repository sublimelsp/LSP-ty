from __future__ import annotations

import re
from functools import cached_property

import sublime

from .constants import PACKAGE_NAME, PLATFORM_ARCH


class VersionManager:
    # https://github.com/astral-sh/ty
    DOWNLOAD_URL_TEMPLATE = "https://github.com/astral-sh/ty/releases/download/{version}/{tarball_name}"

    TARBALL_NAMES = {
        "linux_arm64": "ty-aarch64-unknown-linux-gnu.tar.gz",
        "linux_x64": "ty-x86_64-unknown-linux-gnu.tar.gz",
        "osx_arm64": "ty-aarch64-apple-darwin.tar.gz",
        "osx_x64": "ty-x86_64-apple-darwin.tar.gz",
        "windows_x64": "ty-x86_64-pc-windows-msvc.zip",
        "windows_x86": "ty-i686-pc-windows-msvc.zip",
    }
    """`platform_arch`-specific tarball names for the server."""
    THIS_TARBALL_NAME = TARBALL_NAMES[PLATFORM_ARCH]

    TARBALL_BIN_PATHS = {
        "linux_arm64": "ty-aarch64-unknown-linux-gnu/ty",
        "linux_x64": "ty-x86_64-unknown-linux-gnu/ty",
        "osx_arm64": "ty-aarch64-apple-darwin/ty",
        "osx_x64": "ty-x86_64-apple-darwin/ty",
        "windows_x64": "ty.exe",
        "windows_x86": "ty.exe",
    }
    """`platform_arch`-specific relative path of the server executable in the tarball."""
    THIS_TARBALL_BIN_PATH = TARBALL_BIN_PATHS[PLATFORM_ARCH]

    @cached_property
    def server_version(self) -> str:
        """The server version without a "v" prefix."""
        if m := re.search(
            r"^ty==(.+)",
            sublime.load_resource(f"Packages/{PACKAGE_NAME}/requirements.txt"),
            re.MULTILINE,
        ):
            return m.group(1).strip()
        raise ValueError("Failed to parse server version from requirements.txt")

    @cached_property
    def download_url(self) -> str:
        return self.DOWNLOAD_URL_TEMPLATE.format(version=self.server_version, tarball_name=self.THIS_TARBALL_NAME)

    @cached_property
    def download_hash_url(self) -> str:
        return f"{self.download_url}.sha256"


version_manager = VersionManager()
