"""Jinja filters: Greek-style number and currency formatting."""
from __future__ import annotations


def gr_number(n: float | int | None, decimals: int = 2) -> str:
    """Format a number Greek-style: 1234567.5 -> '1.234.567,50'."""
    if n is None or n == "":
        return ""
    try:
        s = f"{float(n):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(n)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def eur(n: float | int | None) -> str:
    """Format a number as Greek euros: 1234567.5 -> '1.234.567,50 €'."""
    if n is None or n == "":
        return ""
    return f"{gr_number(n)} €"


def eur_short(n: float | int | None) -> str:
    """Compact euro format for KPI cards: 1234567.5 -> '1,23 M €', 528774383 -> '528,77 M €'."""
    if n is None:
        return ""
    try:
        v = float(n)
    except (TypeError, ValueError):
        return str(n)
    if abs(v) >= 1_000_000_000:
        return f"{gr_number(v / 1_000_000_000, 2)} B €"
    if abs(v) >= 1_000_000:
        return f"{gr_number(v / 1_000_000, 2)} M €"
    if abs(v) >= 1_000:
        return f"{gr_number(v / 1_000, 1)} K €"
    return eur(v)


# Heuristic: Greek personal-name patterns (X ΤΟΥ Y / X TOY Y) and missing legal-form suffix.
_LEGAL_SUFFIXES = (
    " Α.Ε.", " ΑΕ", " Α.Ε ", " A.E.", " ΑΤΕ", " Α.Τ.Ε.",
    " ΕΠΕ", " Ε.Π.Ε.", " ΙΚΕ", " Ι.Κ.Ε.",
    " ΟΕ", " Ο.Ε.", " ΕΕ", " Ε.Ε.",
    " AE", " ATE", " EPE", " IKE",
    "ΑΝΩΝΥΜ",
    "ΕΤΑΙΡ",
    "ΟΜΟΡΡΥΘΜ",
    "ΕΤΕΡΟΡΡΥΘΜ",
    "Ε.Π.Ε",
    "Ο.Ε.",
    "ΕΕ",
)


def is_natural_person(name: str | None) -> bool:
    """Best-effort heuristic: treat 'X ΤΟΥ Y' / 'X TOY Y' as natural persons,
    unless they contain a Greek legal-form indicator."""
    if not name:
        return False
    upper = name.upper()
    if any(s.strip() in upper for s in _LEGAL_SUFFIXES):
        return False
    return " ΤΟΥ " in upper or " TOY " in upper or " ΤΗΣ " in upper or " THS " in upper


def redflag_class(pct_direct: float | None) -> str:
    """Return CSS class for the direct-assignment % badge."""
    if pct_direct is None:
        return ""
    if pct_direct >= 100:
        return "redflag redflag-red"
    if pct_direct >= 80:
        return "redflag redflag-amber"
    return "redflag redflag-neutral"


def register(app):
    """Register all filters on a Flask app."""
    app.jinja_env.filters["gr_number"] = gr_number
    app.jinja_env.filters["eur"] = eur
    app.jinja_env.filters["eur_short"] = eur_short
    app.jinja_env.filters["is_natural_person"] = is_natural_person
    app.jinja_env.filters["redflag_class"] = redflag_class
