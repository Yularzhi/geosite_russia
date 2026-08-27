# ── Backward-compatibility wrappers ─────────────────────────────────────────
# Old paths used by legacy CI references and users — just re-export from the
# real package so nothing breaks if someone does `from scripts.build_*`.

from geosite_russia.build_lists import main as build_main  # noqa: F401
from geosite_russia.build_singbox_rulesets import main as singbox_main  # noqa: F401
from geosite_russia.shared import *  # noqa: F401, F403
