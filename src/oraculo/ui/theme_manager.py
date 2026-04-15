"""
Modulo: oraculo.ui.theme_manager
Proposito: Temas visuales por perfil de seguridad.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Theme:
    name: str
    accent: str
    accent_secondary: str
    badge_color: str
    description: str


THEMES: dict[str, Theme] = {
    "basic": Theme(
        name="basic",
        accent="#38BDF8",
        accent_secondary="#2563EB",
        badge_color="#22C55E",
        description="Modo rapido — Sin restricciones de seguridad",
    ),
    "enterprise": Theme(
        name="enterprise",
        accent="#A855F7",
        accent_secondary="#7C3AED",
        badge_color="#F59E0B",
        description="Modo empresa — Auth obligatorio, HMAC habilitado",
    ),
    "banking": Theme(
        name="banking",
        accent="#EF4444",
        accent_secondary="#DC2626",
        badge_color="#EF4444",
        description="Modo bancario — Air-gap, crypto-shred, audit chain",
    ),
}


def get_theme(profile: str) -> Theme:
    return THEMES.get(profile, THEMES["basic"])


def get_theme_css_vars(profile: str) -> str:
    theme = get_theme(profile)
    return (
        f"--accent:{theme.accent};"
        f"--accent-secondary:{theme.accent_secondary};"
        f"--badge-color:{theme.badge_color};"
    )


def list_themes() -> list[str]:
    return list(THEMES.keys())
