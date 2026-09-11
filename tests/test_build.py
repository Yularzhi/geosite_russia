"""Tests for ru_geosite builder (offline, no network)."""

from __future__ import annotations

import pytest

from ru_geosite import build_lists, shared
from ru_geosite.build_singbox_rulesets import build_rule_set, parse_rule

# ── shared ────────────────────────────────────────────────────────────────


def test_strip_inline_comment():
    assert shared.strip_inline_comment("example.com # comment") == "example.com"
    assert shared.strip_inline_comment("# full") == ""
    assert shared.strip_inline_comment("  a.com  ") == "a.com"


def test_load_domain_file_filters_comments(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("a.com\n# c\n\nb.com # inline\n", encoding="utf-8")
    assert shared.load_domain_file(f) == ["a.com", "b.com"]
    assert shared.load_domain_file(tmp_path / "missing") == []


def test_root_tags_includes_ru_blocked():
    assert "ru-blocked" in shared.ROOT_TAGS
    assert set(build_lists.REQUIRED_MIN_DOMAINS) >= set(shared.ROOT_TAGS)


# ── normalize ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Example.COM:443", "example.com"),
        ("example.com:", "example.com"),
        ("example.com:abc", None),  # invalid port rejected
        ("::1", None),
        ("2001:db8::1", None),
        ("привет.рф", "xn--b1agh1afp.xn--p1ai"),
        ("XN--B1AGH1AFP.XN--P1AI", "xn--b1agh1afp.xn--p1ai"),
        ("bad_host.com", None),
        ("x.local", None),
        ("1.2.3.4", None),
    ],
)
def test_normalize_text_domain(raw, expected):
    assert build_lists.normalize_text_domain(raw) == expected


# ── upstream parsing ──────────────────────────────────────────────────────


def test_parse_upstream_line_include_with_attrs():
    assert build_lists.parse_upstream_line("include:google @ads") == ("include", "google", {"ads"})


def test_flatten_rules_resolves_includes_and_attrs(monkeypatch):
    build_lists.get_config()  # load config before monkeypatching config-backed globals
    pages = {
        "https://dlc/a": "include:b @ads\nkeep.com\n",
        "https://dlc/b": "full:x.com @ads\nkeyword:y @ads\nplain.com\n",
    }
    monkeypatch.setattr(build_lists, "DLC_BASE", "https://dlc/")
    monkeypatch.setattr(build_lists, "fetch_text", lambda url, **kw: pages[url])
    build_lists.clear_flatten_cache()
    try:
        # include:b @ads pulls only @ads rules from b; attrs are stripped from values
        assert build_lists.flatten_rules("a") == ["full:x.com", "keyword:y", "keep.com"]
    finally:
        build_lists.clear_flatten_cache()


def test_flatten_rules_cycle_safe(monkeypatch):
    build_lists.get_config()  # load config before monkeypatching config-backed globals
    pages = {"https://dlc/a": "include:b\n", "https://dlc/b": "include:a\nx.com\n"}
    monkeypatch.setattr(build_lists, "DLC_BASE", "https://dlc/")
    monkeypatch.setattr(build_lists, "fetch_text", lambda url, **kw: pages[url])
    build_lists.clear_flatten_cache()
    try:
        assert build_lists.flatten_rules("a") == ["x.com"]
    finally:
        build_lists.clear_flatten_cache()


def test_flatten_rules_cached(monkeypatch):
    build_lists.get_config()  # load config before monkeypatching config-backed globals
    calls = []
    monkeypatch.setattr(build_lists, "DLC_BASE", "https://dlc/")

    def fake_fetch(url, **kw):
        calls.append(url)
        return "x.com\n"

    monkeypatch.setattr(build_lists, "fetch_text", fake_fetch)
    build_lists.clear_flatten_cache()
    try:
        build_lists.flatten_rules("a")
        build_lists.flatten_rules("a")
        assert len(calls) == 1
    finally:
        build_lists.clear_flatten_cache()


# ── ru exclusion ──────────────────────────────────────────────────────────


def test_is_ru_excluded_domain():
    build_lists.get_config()
    assert build_lists.is_ru_excluded_domain("example.ru")
    assert build_lists.is_ru_excluded_domain("sub.yandex.ru")
    assert build_lists.is_ru_excluded_domain("vk.com")
    assert not build_lists.is_ru_excluded_domain("example.com")


# ── Direct/Proxy conflict ─────────────────────────────────────────────────


def test_is_direct_domain_matches_parent_domain():
    direct = {"bluestacks.com", "licard.com"}
    assert build_lists.is_direct_domain("bluestacks.com", direct)
    assert build_lists.is_direct_domain("api.bluestacks.com", direct)
    assert not build_lists.is_direct_domain("notbluestacks.com", direct)
    assert not build_lists.is_direct_domain("bluestacks.com.evil.net", direct)


def _stub_ru_blocked(monkeypatch, tmp_path, *, antifilter, proxy, manual):
    """Patch build_ru_blocked inputs: two remote lists, manual file, Direct set."""
    build_lists.get_config()
    monkeypatch.setattr(build_lists, "DATA_DIR", tmp_path)
    monkeypatch.setattr(build_lists, "ANTIFILTER_RU_BLOCKED_URL", "antifilter")
    monkeypatch.setattr(build_lists, "PROXY_URL", "proxy")
    lists = {"antifilter": antifilter, "proxy": proxy}
    monkeypatch.setattr(build_lists, "fetch_lines", lambda url: lists[url])
    monkeypatch.setattr(build_lists, "load_domain_file", lambda *a, **kw: list(manual))
    # Direct set = DLC half (bluestacks.com) + direct-file half (licard.com)
    monkeypatch.setattr(build_lists, "flatten_rules", lambda tag, *a, **kw: ["bluestacks.com"])
    monkeypatch.setattr(build_lists, "load_category_ru_direct_domains", lambda: ["licard.com"])


def test_ru_blocked_drops_direct_conflicts_from_every_source(monkeypatch, tmp_path):
    _stub_ru_blocked(
        monkeypatch,
        tmp_path,
        antifilter=["bluestacks.com", "novayagazeta.ru"],
        proxy=["api.bluestacks.com", "netflix.com", "licard.com"],
        manual=["licard.com", "speedtest.net"],
    )
    assert build_lists.build_ru_blocked() == ["netflix.com", "novayagazeta.ru", "speedtest.net"]


def test_ru_blocked_tld_exclusion_applies_only_to_proxy_list(monkeypatch, tmp_path):
    _stub_ru_blocked(
        monkeypatch,
        tmp_path,
        antifilter=["tvrain.ru"],
        proxy=["rutracker.ru", "netflix.com"],
        manual=["jut.su"],
    )
    result = build_lists.build_ru_blocked()
    assert "tvrain.ru" in result  # antifilter kept as is
    assert "jut.su" in result  # manual entries are explicit intent
    assert "rutracker.ru" not in result  # proxy list cleaned by .ru/.su/.рф


def test_flat_root_tags_lowercase_domain_rules_only(monkeypatch, tmp_path):
    build_lists.get_config()
    monkeypatch.setattr(build_lists, "DATA_DIR", tmp_path)
    monkeypatch.setattr(build_lists, "ROOT_TAGS", ["category-ru"])
    monkeypatch.setattr(
        build_lists,
        "flatten_rules",
        lambda tag, *a, **kw: ["xn--80AGLFYFK.xn--p1ai", "regexp:(?i)Foo", "keyword:AdS"],
    )
    monkeypatch.setattr(build_lists, "load_category_ru_direct_domains", lambda: [])
    build_lists.build_flat_root_tags()
    lines = (tmp_path / "category-ru").read_text(encoding="utf-8").splitlines()
    assert "xn--80aglfyfk.xn--p1ai" in lines
    assert "regexp:(?i)Foo" in lines  # patterns stay case-sensitive
    assert "keyword:AdS" in lines


# ── sing-box ──────────────────────────────────────────────────────────────


def test_parse_rule_variants():
    assert parse_rule("full:example.com") == ("domain", "example.com")
    assert parse_rule("keyword:ads") == ("domain_keyword", "ads")
    assert parse_rule("example.com") == ("domain_suffix", "example.com")
    assert parse_rule("domain:example.com") == ("domain_suffix", "example.com")
    assert parse_rule("include:other") is None
    assert parse_rule("# comment") is None


def test_build_rule_set(tmp_path, monkeypatch):
    (tmp_path / "t").write_text("full:a.com\nexample.com\nkeyword:ads\n", encoding="utf-8")
    monkeypatch.setattr("ru_geosite.build_singbox_rulesets.DATA_DIR", tmp_path)
    rs = build_rule_set("t")
    assert rs["version"] == 4
    flat = {k: v for r in rs["rules"] for k, v in r.items()}
    assert flat == {"domain": ["a.com"], "domain_suffix": ["example.com"], "domain_keyword": ["ads"]}


def test_validate_output_missing_and_min(tmp_path):
    (tmp_path / "a").write_text("x.com\n", encoding="utf-8")
    errs = build_lists.validate_output({"a": 5, "b": 1}, data_dir=tmp_path)
    assert any("[a] Only 1" in e for e in errs)
    assert any("[b] File missing" in e for e in errs)
    assert build_lists.validate_output({"a": 1}, data_dir=tmp_path) == []


# ── required-source failure handling ──────────────────────────────────────


def test_build_ru_blocked_fails_without_antifilter(monkeypatch, tmp_path):
    build_lists.get_config()
    monkeypatch.setattr(build_lists, "DATA_DIR", tmp_path)
    monkeypatch.setattr(build_lists, "flatten_rules", lambda tag, required_attrs=None, seen=None: [])

    def boom(url, **kw):
        raise OSError("down")

    monkeypatch.setattr(build_lists, "fetch_lines", boom)
    with pytest.raises(RuntimeError):
        build_lists.build_ru_blocked()


def test_build_ads_fails_when_all_hagezi_mirrors_down(monkeypatch, tmp_path):
    build_lists.get_config()
    monkeypatch.setattr(build_lists, "DATA_DIR", tmp_path)
    monkeypatch.setattr(build_lists, "flatten_rules", lambda tag, required_attrs=None, seen=None: ["x.com"])

    def boom(url, **kw):
        raise OSError("down")

    monkeypatch.setattr(build_lists, "fetch_text", boom)
    with pytest.raises(RuntimeError):
        build_lists.build_ads()
