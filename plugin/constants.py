from __future__ import annotations

import sublime

assert __package__

PACKAGE_NAME = __package__.partition(".")[0]

PLATFORM_ARCH = f"{sublime.platform()}_{sublime.arch()}"
