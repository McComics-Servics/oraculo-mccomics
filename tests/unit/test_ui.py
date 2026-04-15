"""Tests para F8 — UI (window, theme_manager, assets)."""
from __future__ import annotations
import json
from pathlib import Path

from oraculo.ui.window import (
    get_index_html, launch_window_headless,
    ASSETS_DIR, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
)
from oraculo.ui.theme_manager import (
    get_theme, get_theme_css_vars, list_themes, THEMES, Theme,
)


# ── Assets ──────────────────────────────────────────

class TestAssets:
    def test_index_html_exists(self):
        path = ASSETS_DIR / "index.html"
        assert path.exists()

    def test_index_html_not_empty(self):
        html = get_index_html()
        assert len(html) > 1000

    def test_index_html_has_doctype(self):
        html = get_index_html()
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_index_html_has_10_tabs(self):
        html = get_index_html()
        assert html.count('data-tab=') == 10

    def test_index_html_has_10_panels(self):
        html = get_index_html()
        assert html.count('id="panel-') == 10

    def test_index_html_has_3_profile_buttons(self):
        html = get_index_html()
        assert html.count('data-profile=') == 3

    def test_index_html_has_glassmorphism(self):
        html = get_index_html()
        assert "backdrop-filter" in html
        assert "blur(" in html

    def test_index_html_has_mccomics_branding(self):
        html = get_index_html()
        assert "McComics" in html
        assert "#2563EB" in html

    def test_index_html_has_search_input(self):
        html = get_index_html()
        assert 'id="queryInput"' in html

    def test_index_html_has_pywebview_api_calls(self):
        html = get_index_html()
        assert "pywebview.api." in html

    def test_index_html_has_sse_or_query_function(self):
        html = get_index_html()
        assert "doQuery" in html

    def test_index_html_tab_names(self):
        html = get_index_html()
        for tab in ["query", "index", "training", "status", "model", "symbols", "compliance", "settings", "log", "about"]:
            assert f'data-tab="{tab}"' in html

    def test_index_html_profile_names(self):
        html = get_index_html()
        for p in ["basic", "enterprise", "banking"]:
            assert f'data-profile="{p}"' in html

    def test_index_html_has_training_panel(self):
        html = get_index_html()
        assert "auto_training" in html or "toggle_auto_training" in html
        assert "Re-entrenar" in html or "re-entrenar" in html.lower() or "retrain" in html.lower()

    def test_index_html_has_compliance_panel(self):
        html = get_index_html()
        assert "compliance" in html.lower()
        assert "air" in html.lower()

    def test_index_html_has_download_model(self):
        html = get_index_html()
        assert "download_model" in html

    def test_index_html_has_data_dir_visible(self):
        html = get_index_html()
        assert ".oraculo" in html

    def test_index_html_has_honest_disclaimers(self):
        html = get_index_html()
        assert "NO entiende" in html or "no entiende" in html or "no reemplaza" in html.lower()

    def test_index_html_has_bsl_license(self):
        html = get_index_html()
        assert "BSL" in html


# ── Window ──────────────────────────────────────────

class TestWindow:
    def test_window_constants(self):
        assert WINDOW_WIDTH == 1200
        assert WINDOW_HEIGHT == 800
        assert "Oraculo" in WINDOW_TITLE

    def test_headless_launch(self):
        ctx = {"version": "4.0.0", "active_profile": "basic"}
        result = launch_window_headless(ctx)
        assert result["title"] == WINDOW_TITLE
        assert result["width"] == 1200
        assert result["height"] == 800
        assert result["html_length"] > 1000
        assert result["has_bridge"] is True

    def test_assets_dir_exists(self):
        assert ASSETS_DIR.exists()
        assert ASSETS_DIR.is_dir()


# ── Theme Manager ───────────────────────────────────

class TestThemeManager:
    def test_all_profiles_have_themes(self):
        for profile in ["basic", "enterprise", "banking"]:
            theme = get_theme(profile)
            assert isinstance(theme, Theme)
            assert theme.name == profile

    def test_unknown_profile_defaults_to_basic(self):
        theme = get_theme("nonexistent")
        assert theme.name == "basic"

    def test_theme_css_vars(self):
        css = get_theme_css_vars("enterprise")
        assert "--accent:" in css
        assert "--accent-secondary:" in css
        assert "--badge-color:" in css

    def test_list_themes(self):
        themes = list_themes()
        assert "basic" in themes
        assert "enterprise" in themes
        assert "banking" in themes
        assert len(themes) == 3

    def test_basic_theme_colors(self):
        theme = get_theme("basic")
        assert theme.accent == "#38BDF8"

    def test_enterprise_theme_colors(self):
        theme = get_theme("enterprise")
        assert theme.accent == "#A855F7"

    def test_banking_theme_colors(self):
        theme = get_theme("banking")
        assert theme.accent == "#EF4444"

    def test_theme_descriptions(self):
        for profile in ["basic", "enterprise", "banking"]:
            theme = get_theme(profile)
            assert len(theme.description) > 10

    def test_themes_dict_complete(self):
        assert len(THEMES) == 3
        for k, v in THEMES.items():
            assert v.accent.startswith("#")
            assert v.accent_secondary.startswith("#")
