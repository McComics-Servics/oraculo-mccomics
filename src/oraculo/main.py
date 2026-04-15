"""
Entry point del daemon Oraculo McComics v4.0.
Integra las 7 capas via OraculoApp.
"""
from __future__ import annotations
import sys

from oraculo.app import run_app


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    mode = "ui"
    if "--server" in argv:
        mode = "server"
    elif "--headless" in argv:
        mode = "headless"
    return run_app(mode=mode)


if __name__ == "__main__":
    sys.exit(main())
