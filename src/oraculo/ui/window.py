"""
Modulo: oraculo.ui.window
Proposito: Lanzador de la ventana pywebview con js_api (IPCBridge).
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"
WINDOW_TITLE = "El Oraculo McComics v4.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600


def get_index_html() -> str:
    index = ASSETS_DIR / "index.html"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "<html><body><h1>Error: index.html no encontrado</h1></body></html>"


def launch_window(app_context: dict[str, Any], debug: bool = False) -> None:
    """Lanza la ventana pywebview con la UI completa."""
    try:
        import webview
    except ImportError:
        logger.error("pywebview no instalado. pip install pywebview")
        print("ERROR: pywebview no instalado. Ejecutar: pip install pywebview")
        return

    from oraculo.api.ipc_bridge import IPCBridge
    bridge = IPCBridge(app_context)

    window = webview.create_window(
        WINDOW_TITLE,
        html=get_index_html(),
        js_api=bridge,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
        resizable=True,
        text_select=True,
    )

    app_context["window"] = window
    logger.info("Lanzando ventana: %s (%dx%d)", WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT)
    webview.start(debug=debug)


def launch_window_headless(app_context: dict[str, Any]) -> dict[str, Any]:
    """Version sin pywebview para testing — retorna config de ventana."""
    return {
        "title": WINDOW_TITLE,
        "width": WINDOW_WIDTH,
        "height": WINDOW_HEIGHT,
        "html_length": len(get_index_html()),
        "has_bridge": True,
    }
